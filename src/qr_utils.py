from __future__ import annotations
import json
import zlib
import binascii
from pathlib import Path
from typing import List, Tuple

try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L
except Exception as e:  # pragma: no cover
    qrcode = None
    ERROR_CORRECT_L = None


APP = b"SMEOW"
VER = 1
SINGLE_QR_SAFE_CAP = 2500


def _build_single_payload(comp: bytes) -> bytes:
    crc = f"{(binascii.crc32(comp) & 0xFFFFFFFF):08X}".encode("ascii")
    header = b"%s|%d|S|%s|" % (APP, VER, crc)
    return header + comp


def _iter_multi_payloads(comp: bytes):
    crc = f"{(binascii.crc32(comp) & 0xFFFFFFFF):08X}".encode("ascii")
    MAX_PAYLOAD = 1000
    parts = [comp[i : i + MAX_PAYLOAD] for i in range(0, len(comp), MAX_PAYLOAD)]
    total = len(parts)
    for idx, p in enumerate(parts, start=1):
        header = b"%s|%d|M|%d|%d|%s|" % (APP, VER, total, idx, crc)
        yield header + p


def make_qr_pil_images_from_output(path: Path) -> Tuple[bool, "List[object]"]:
    if qrcode is None:
        raise RuntimeError("缺少 qrcode 库，无法生成二维码")

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    comp = zlib.compress(raw, level=9)

    content = _build_single_payload(comp)
    qr = qrcode.QRCode(
        version=None, error_correction=ERROR_CORRECT_L, box_size=8, border=2
    )

    images = []
    if len(content) <= SINGLE_QR_SAFE_CAP:
        qr.clear()
        qr.add_data(content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        images.append(img)
        return False, images

    # 多帧
    for payload in _iter_multi_payloads(comp):
        qr.clear()
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        images.append(img)
    return True, images
