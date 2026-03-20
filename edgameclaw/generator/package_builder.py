# Created by Yuqi Hang (github.com/yh2072)
"""Build and write the game data package (JSON and optional encrypted) for player-based playback.

Package format: JSON with config, script, pixel_art_js, minigames_js, cover_js, styleBlock, ui, title, subtitle, total_chapters.
Encryption at rest: if GAME_PACKAGE_SECRET is set, also write game.pkg.enc (Fernet).
JS in package: when OBFS_JS=1 or when writing encrypted, minify/obfuscate minigames_js, pixel_art_js, cover_js via terser (optional).
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .assembler import get_rendered_style_block, get_theme_css, _build_init_js


def _obfuscate_js(code: str) -> str:
    """Minify/mangle JS with terser (subprocess). Returns original code if terser unavailable or fails."""
    if not code or not code.strip():
        return code
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp = f.name
        out = subprocess.run(
            ["npx", "-y", "terser", tmp, "--compress", "--mangle", "--no-annotations"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(__file__) or ".",
        )
        try:
            os.unlink(tmp)
        except OSError:
            pass
        if out.returncode == 0 and out.stdout:
            return out.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return code


def build_package_dict(content: dict, template_dir: str, obfuscate_js_fields: bool = False) -> dict:
    """Build the package payload from the same content dict used by assemble().

    Args:
        content: Dict with config, script, pixel_art_js, minigame_data, theme (name), simulation_codes, cover_js.
                 We need to produce minigames_js the same way assembler does — but assembler builds it from
                 content + template_dir. So we either pass pre-built minigames_js in content, or we need to
                 duplicate the minigame assembly. Prefer: pipeline passes minigames_js in content when calling
                 write_package (pipeline already has the full content and can pass the same minigames_js string
                 that assembler uses). So content should have: config, script, pixel_art_js, minigames_js,
                 cover_js, theme (name), ui (or we get from config). And we need styleBlock: render from template.
    """
    config = content["config"]
    script = content["script"]
    pixel_art_js = content["pixel_art_js"]
    minigames_js = content.get("minigames_js", "")
    cover_js = content.get("cover_js", "")
    if obfuscate_js_fields:
        pixel_art_js = _obfuscate_js(pixel_art_js)
        minigames_js = _obfuscate_js(minigames_js)
        cover_js = _obfuscate_js(cover_js)
    theme_name = content.get("theme", "pink-cute")
    theme_css = get_theme_css(theme_name)
    ui = config.get("ui") or {}

    style_block = get_rendered_style_block(template_dir, theme_css, ui)
    init_js = _build_init_js()

    return {
        "v": 1,
        "config": config,
        "script": script,
        "pixel_art_js": pixel_art_js,
        "minigames_js": minigames_js,
        "cover_js": cover_js,
        "init_js": init_js,
        "styleBlock": style_block,
        "theme": theme_css,
        "ui": ui,
        "title": config.get("title", "EdGame"),
        "subtitle": config.get("subtitle", ""),
        "total_chapters": config.get("totalChapters", 6),
    }


def write_package(
    content: dict,
    template_dir: str,
    output_dir: str,
    *,
    write_json: bool = True,
    write_encrypted: bool | None = None,
) -> tuple[str | None, str | None]:
    """Build the package and write game.pkg.json and optionally game.pkg.enc.

    Args:
        content: Same dict as for assemble(); must include minigames_js (built by pipeline before calling this).
        template_dir: Path to engine/ for get_rendered_style_block.
        output_dir: Directory to write into (e.g. game dir).
        write_json: If True, write game.pkg.json.
        write_encrypted: If True, encrypt and write game.pkg.enc. If None, use GAME_PACKAGE_SECRET env.
    When OBFS_JS=1 or when writing encrypted, JS fields (minigames_js, pixel_art_js, cover_js) are minified with terser.

    Returns:
        (path_to_json_or_none, path_to_enc_or_none).
    """
    do_encrypt = write_encrypted if write_encrypted is not None else bool(os.environ.get("GAME_PACKAGE_SECRET"))
    obfuscate = os.environ.get("OBFS_JS", "").strip().lower() in ("1", "true", "yes") or do_encrypt
    pkg = build_package_dict(content, template_dir, obfuscate_js_fields=obfuscate)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "game.pkg.json" if write_json else None
    enc_path = out / "game.pkg.enc"

    if write_json and json_path:
        json_path.write_text(json.dumps(pkg, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [package] Wrote {json_path.relative_to(out.parent.parent)}", file=sys.stderr)

    if do_encrypt:
        secret = os.environ.get("GAME_PACKAGE_SECRET", "").encode("utf-8")
        if not secret or len(secret) < 16:
            print("  [package] GAME_PACKAGE_SECRET missing or too short; skip encryption", file=sys.stderr)
        else:
            try:
                from cryptography.fernet import Fernet
                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
                import base64
                kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b"edgame_pkg_salt", iterations=100_000)
                key = base64.urlsafe_b64encode(kdf.derive(secret))
                f = Fernet(key)
                payload = json.dumps(pkg, ensure_ascii=False).encode("utf-8")
                enc_path.write_bytes(f.encrypt(payload))
                print(f"  [package] Wrote encrypted {enc_path.relative_to(out.parent.parent)}", file=sys.stderr)
                return (str(json_path) if json_path else None, str(enc_path))
            except Exception as e:
                print(f"  [package] Encryption failed: {e}", file=sys.stderr)

    return (str(json_path) if json_path else None, None)


def decrypt_package(enc_path: str | Path) -> dict:
    """Decrypt game.pkg.enc and return the package dict. Used by the server when serving the package."""
    secret = os.environ.get("GAME_PACKAGE_SECRET", "").encode("utf-8")
    if not secret or len(secret) < 16:
        raise ValueError("GAME_PACKAGE_SECRET required for decryption")
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b"edgame_pkg_salt", iterations=100_000)
    key = base64.urlsafe_b64encode(kdf.derive(secret))
    f = Fernet(key)
    enc_path = Path(enc_path)
    cipher = enc_path.read_bytes()
    return json.loads(f.decrypt(cipher).decode("utf-8"))
