import io, base64
import pyotp
import qrcode


def generate_secret() -> str:
    return pyotp.random_base32()


def verify_code(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code.strip(), valid_window=1)


def get_qr_base64(secret: str, username: str, issuer: str = "BK-Moph Notify") -> str:
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()
