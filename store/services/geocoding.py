import logging
import re
import urllib.parse
from datetime import date, timedelta
import requests
from django.conf import settings
from django.db.models import Q

logger = logging.getLogger(__name__)

INDIAN_PINCODE_REGEX = re.compile(r'^[1-9][0-9]{5}$')


def clean_pincode(val):
    """Extract a clean 6-digit Indian pincode string or None."""
    if not val:
        return None
    cleaned = re.sub(r'[^0-9]', '', str(val).strip())
    if len(cleaned) == 6 and INDIAN_PINCODE_REGEX.match(cleaned):
        return cleaned
    return None


def reverse_geocode(latitude, longitude):
    """
    Perform real reverse geocoding using the configured geocoding provider.
    Supported providers: 'nominatim', 'opencage', 'google', 'mapbox', 'here'.

    Returns:
        dict: {
            'success': bool,
            'pincode': str or None,
            'locality': str,
            'city': str,
            'state': str,
            'formatted_address': str,
            'provider': str,
            'error': str (if success is False),
            'error_type': str (if success is False)
        }
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (ValueError, TypeError):
        return {
            'success': False,
            'error_type': 'invalid_coordinates',
            'error': 'Invalid latitude or longitude coordinates provided.'
        }

    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return {
            'success': False,
            'error_type': 'out_of_bounds',
            'error': 'Coordinates are out of geographical range.'
        }

    provider = getattr(settings, 'GEOCODING_PROVIDER', 'nominatim').lower().strip()
    api_key = getattr(settings, 'GEOCODING_API_KEY', '').strip()

    # If provider requires an API key and none is provided
    if provider in ('opencage', 'google', 'mapbox', 'here') and not api_key:
        logger.warning(f"Geocoding provider '{provider}' selected but GEOCODING_API_KEY is missing.")
        return {
            'success': False,
            'error_type': 'provider_not_configured',
            'error': f"Geocoding provider '{provider}' is configured but missing an API key. Please enter your 6-digit pincode manually."
        }

    timeout = 6  # seconds
    headers = {
        'User-Agent': 'FoodBasket-GroceryDelivery/2.0 (contact@foodbasket.store; +https://foodgrocery-store.onrender.com)',
        'Accept': 'application/json',
    }

    try:
        if provider == 'opencage':
            url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={api_key}&no_annotations=1&language=en"
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            results = data.get('results', [])
            if not results:
                return {'success': False, 'error_type': 'no_results', 'error': 'No address found for these coordinates.'}
            first = results[0]
            components = first.get('components', {})
            raw_postcode = components.get('postcode')
            locality = components.get('suburb') or components.get('neighbourhood') or components.get('road') or components.get('quarter') or ''
            city = components.get('city') or components.get('town') or components.get('county') or ''
            state = components.get('state') or ''
            formatted = first.get('formatted', '')

        elif provider == 'google':
            url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={api_key}&language=en"
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            results = data.get('results', [])
            if not results:
                return {'success': False, 'error_type': 'no_results', 'error': 'No address found for these coordinates.'}
            raw_postcode = None
            locality = ''
            city = ''
            state = ''
            formatted = results[0].get('formatted_address', '')
            for r in results:
                for comp in r.get('address_components', []):
                    types = comp.get('types', [])
                    if 'postal_code' in types and not raw_postcode:
                        raw_postcode = comp.get('long_name')
                    if ('sublocality' in types or 'sublocality_level_1' in types) and not locality:
                        locality = comp.get('long_name')
                    if 'locality' in types and not city:
                        city = comp.get('long_name')
                    if 'administrative_area_level_1' in types and not state:
                        state = comp.get('long_name')

        elif provider == 'mapbox':
            url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{lon},{lat}.json?types=postcode,locality,place,address&access_token={api_key}"
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            features = data.get('features', [])
            if not features:
                return {'success': False, 'error_type': 'no_results', 'error': 'No address found for these coordinates.'}
            raw_postcode = None
            locality = ''
            city = ''
            state = ''
            formatted = features[0].get('place_name', '')
            for f in features:
                f_types = f.get('place_type', [])
                if 'postcode' in f_types and not raw_postcode:
                    raw_postcode = f.get('text')
                for ctx in f.get('context', []):
                    ctx_id = ctx.get('id', '')
                    if ctx_id.startswith('postcode') and not raw_postcode:
                        raw_postcode = ctx.get('text')
                    elif ctx_id.startswith('locality') and not locality:
                        locality = ctx.get('text')
                    elif ctx_id.startswith('place') and not city:
                        city = ctx.get('text')
                    elif ctx_id.startswith('region') and not state:
                        state = ctx.get('text')

        elif provider == 'here':
            url = f"https://revgeocode.search.hereapi.com/v1/revgeocode?at={lat},{lon}&lang=en&apiKey={api_key}"
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            items = data.get('items', [])
            if not items:
                return {'success': False, 'error_type': 'no_results', 'error': 'No address found for these coordinates.'}
            addr = items[0].get('address', {})
            raw_postcode = addr.get('postalCode')
            locality = addr.get('district') or addr.get('subdistrict') or ''
            city = addr.get('city') or addr.get('county') or ''
            state = addr.get('state') or ''
            formatted = addr.get('label', '')

        else:
            # Default: OpenStreetMap Nominatim (works out of the box with standard respectful User-Agent)
            url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}&addressdetails=1&zoom=18"
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            if 'error' in data:
                return {'success': False, 'error_type': 'no_results', 'error': data.get('error', 'Location not found.')}
            address = data.get('address', {})
            raw_postcode = address.get('postcode')
            locality = (
                address.get('suburb') or address.get('neighbourhood') or
                address.get('residential') or address.get('road') or
                address.get('quarter') or address.get('village') or ''
            )
            city = address.get('city') or address.get('town') or address.get('municipality') or address.get('county') or ''
            state = address.get('state') or ''
            formatted = data.get('display_name', '')

        # Sanitize pincode
        clean_pin = clean_pincode(raw_postcode)
        if not clean_pin:
            # Try to search formatted string for 6-digit postal code pattern
            match = re.search(r'\b([1-9][0-9]{5})\b', formatted)
            if match:
                clean_pin = match.group(1)

        return {
            'success': True,
            'pincode': clean_pin,
            'locality': locality.strip(),
            'city': city.strip(),
            'state': state.strip(),
            'formatted_address': formatted.strip(),
            'latitude': lat,
            'longitude': lon,
            'provider': provider,
        }

    except requests.exceptions.Timeout:
        logger.warning(f"Geocoding request timed out for coordinates ({lat}, {lon})")
        return {
            'success': False,
            'error_type': 'timeout',
            'error': 'Location service request timed out. Please enter your 6-digit pincode manually.'
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Geocoding network error: {e}")
        return {
            'success': False,
            'error_type': 'network_error',
            'error': 'Unable to connect to location service. Please enter your 6-digit pincode manually.'
        }
    except Exception as e:
        logger.error(f"Unexpected error in reverse geocoding: {e}", exc_info=True)
        return {
            'success': False,
            'error_type': 'system_error',
            'error': 'Could not determine your location. Please enter your 6-digit pincode manually.'
        }


def check_pincode_serviceability(pincode, area_name=None, city=None, state=None, latitude=None, longitude=None):
    """
    Check and register serviceability for a 6-digit Indian pincode.
    Automatically finds or creates an active DeliveryArea so detected customer locations
    are immediately serviceable across all marketplace delivery features.

    Returns:
        dict with serviceability status, delivery fee, ETA, and slot information.
    """
    from store.models import DeliveryArea, VendorProfile, DeliverySlot

    clean_pin = clean_pincode(pincode)
    if not clean_pin:
        return {
            'success': False,
            'is_serviceable': False,
            'error_type': 'invalid_format',
            'error': 'Please enter a valid 6-digit Indian pincode (e.g. 625001).'
        }

    # Automatically find or register the delivery area
    area = DeliveryArea.objects.filter(pincode=clean_pin).first()
    if not area:
        area = DeliveryArea.objects.create(
            pincode=clean_pin,
            area_name=area_name or f"Zone {clean_pin}",
            city=city or 'Local Area',
            state=state or '',
            latitude=latitude,
            longitude=longitude,
            delivery_fee=30,
            minimum_order_value=100,
            estimated_delivery_minutes=45,
            is_active=True,
        )
    elif not area.is_active:
        area.is_active = True
        area.save()

    # Check approved vendors servicing this area or marketplace general vendors
    approved_vendors = VendorProfile.objects.filter(status='approved')
    matched_vendors = approved_vendors.filter(
        Q(service_areas=area) | Q(pincode=clean_pin) | Q(assigned_area__icontains=clean_pin)
    ).distinct()

    vendors_count = matched_vendors.count() if matched_vendors.exists() else approved_vendors.count()

    # Check delivery slots for today & tomorrow
    today = date.today()
    slots_qs = DeliverySlot.objects.filter(
        date__gte=today,
        date__lte=today + timedelta(days=1)
    ).order_by('date', 'slot')

    available_slots = []
    for s in slots_qs:
        if s.is_available:
            available_slots.append({
                'id': s.id,
                'date': s.date.strftime('%a, %d %b'),
                'slot_name': s.get_slot_display(),
                'slots_remaining': s.slots_remaining,
            })

    return {
        'success': True,
        'is_serviceable': True,
        'pincode': area.pincode,
        'area_id': area.id,
        'area_name': area.area_name,
        'city': area.city,
        'state': area.state,
        'display_name': area.display_name,
        'delivery_fee': float(area.delivery_fee),
        'minimum_order_value': float(area.minimum_order_value),
        'estimated_delivery_minutes': area.estimated_delivery_minutes,
        'estimated_delivery_text': f"Express delivery in ~{area.estimated_delivery_minutes} mins",
        'approved_vendors_count': max(1, vendors_count),
        'available_slots': available_slots[:4],
    }
