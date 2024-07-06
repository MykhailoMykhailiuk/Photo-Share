from io import BytesIO

import qrcode
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont


def generate_qr_code_with_url(url: str) -> StreamingResponse:
    """The generate_qr_code function generates a QR code from the given URL
    and adds the URL as a caption below the QR code.

    Args:
        url (str): The URL to encode in the QR code.

    Returns:
        StreamingResponse: Containing the QR code image with URL caption.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white").convert("RGB")

    font = ImageFont.load_default()

    draw = ImageDraw.Draw(img)

    text_bbox = draw.textbbox((0, 0), url, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    img_width, img_height = img.size
    # text_width, text_height = draw.textbbox(url, font=font)

    text_position = (0, img_height + 10)

    new_img = Image.new(
        "RGB", (text_width, img_height + text_height + 20), (255, 255, 255)
    )
    new_img.paste(img, (0, 0))

    draw = ImageDraw.Draw(new_img)
    draw.text(text_position, url, fill="black", font=font)

    buf = BytesIO()
    new_img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


def generate_qr_code(url: str) -> StreamingResponse:
    """The generate_qr_code function generates a QR code from the given data.

    Args:
        url (str): The data to encode in the QR code.

    Returns:
        StreamingResponse: Containing the QR code image.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white")

    buf = BytesIO()
    img.save(buf)
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")
