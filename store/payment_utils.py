import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

try:
    import razorpay
    HAS_RAZORPAY = True
except ImportError:
    HAS_RAZORPAY = False


def is_test_or_placeholder_mode():
    key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
    return (
        not key_id or
        not key_secret or
        'placeholder' in key_id.lower() or
        'placeholder' in key_secret.lower() or
        not HAS_RAZORPAY
    )


def get_razorpay_client():
    if is_test_or_placeholder_mode():
        return None
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_razorpay_order(amount_inr, receipt_id, notes=None):
    """
    Creates a Razorpay order in INR (amount in paise).
    If Razorpay keys are not configured or placeholder, returns a safe mock order structure.
    """
    amount_paise = int(round(float(amount_inr) * 100))
    if is_test_or_placeholder_mode():
        mock_id = f"order_mock_{receipt_id}_{int(timezone.now().timestamp())}"
        logger.info("Razorpay in test/mock mode: created simulated order %s for receipt %s (₹%s)", mock_id, receipt_id, amount_inr)
        return {
            'id': mock_id,
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': str(receipt_id),
            'status': 'created',
            'mock': True,
        }

    client = get_razorpay_client()
    order_data = {
        'amount': amount_paise,
        'currency': 'INR',
        'receipt': f"receipt_{receipt_id}",
        'notes': notes or {},
        'payment_capture': '1',
    }
    try:
        rp_order = client.order.create(data=order_data)
        logger.info("Created Razorpay order %s for receipt %s", rp_order.get('id'), receipt_id)
        return rp_order
    except Exception as e:
        logger.error("Error creating Razorpay order: %s", str(e))
        raise


def verify_razorpay_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """
    Verifies Razorpay HMAC signature. Never trust frontend status alone.
    Returns True if valid, False otherwise.
    """
    if not razorpay_order_id or not razorpay_payment_id:
        return False

    if razorpay_order_id.startswith('order_mock_'):
        logger.info("Verified mock Razorpay payment %s for order %s", razorpay_payment_id, razorpay_order_id)
        return True

    client = get_razorpay_client()
    if not client:
        return False

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        })
        logger.info("Successfully verified Razorpay signature for order %s, payment %s", razorpay_order_id, razorpay_payment_id)
        return True
    except Exception as e:
        logger.warning("Razorpay signature verification failed for order %s: %s", razorpay_order_id, str(e))
        return False
