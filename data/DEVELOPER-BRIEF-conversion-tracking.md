# Developer Brief: Google Ads Conversion Tracking Setup

## Problem

Google Ads campaigns send traffic to an advertorial page on `trustedselections.org`. Users read the article, then click through to the Shopify store to purchase. Currently, Google cannot track any purchases because:

1. `trustedselections.org` does NOT have the Google Ads tag installed
2. There is no cross-domain tracking between `trustedselections.org` and the Shopify store
3. When a user clicks the ad and lands on `trustedselections.org`, the Google click ID (`gclid`) is lost when they navigate to Shopify

## User Flow

```
Google Ad click → trustedselections.org (advertorial) → Shopify store → Purchase
                  ^^^^^^^^^^^^^^^^^^^^                   ^^^^^^^^^^^^
                  NEEDS GTAG INSTALLED                   HAS GTAG (via Google channel)
                  NEEDS CROSS-DOMAIN LINKING             NEEDS CROSS-DOMAIN LINKING
```

## What Needs to Be Done

### Task 1: Add Google Ads Global Site Tag to trustedselections.org

Add this snippet to the `<head>` section of EVERY page on `trustedselections.org` (or at minimum, the landing page at `/top-5-best-magnesium-2026`):

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=AW-17196166864"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'AW-17196166864', {
    'linker': {
      'domains': ['trustedselections.org', 'evolancewellness.com']
    }
  });
</script>
```

**Important:** The `linker.domains` array must include BOTH domains. This enables automatic cross-domain tracking — Google will append the `gclid` and `_gl` parameter to links between these domains.

If the site uses Google Tag Manager (GTM) instead of inline gtag, add the Google Ads conversion ID `AW-17196166864` as a new Google Ads tag in GTM, and configure cross-domain linking in the tag settings.

### Task 2: Add Cross-Domain Linker to Shopify's Google Tag

On the Shopify store (likely via the Google & YouTube channel app or GTM), ensure the existing Google tag also has the linker config:

```html
gtag('config', 'AW-17196166864', {
  'linker': {
    'domains': ['trustedselections.org', 'evolancewellness.com']
  }
});
```

If Shopify uses its own Google channel integration, go to:
- Google Ads UI → Admin → Data Streams → Web → Configure Tag Settings → Configure Your Domains
- Add both `trustedselections.org` and `evolancewellness.com` (or whatever the Shopify domain is)

### Task 3: Verify the Purchase Conversion Tag on Shopify

The Purchase conversion event must fire on the Shopify order confirmation (thank you) page. The event snippet is:

```html
<script>
  gtag('event', 'conversion', {
    'send_to': 'AW-17196166864/m7fUCO3BxNkaENDd4odA',
    'value': <ORDER_TOTAL>,
    'currency': 'USD',
    'transaction_id': '<ORDER_ID>'
  });
</script>
```

Replace `<ORDER_TOTAL>` and `<ORDER_ID>` with dynamic Shopify values. If Shopify's Google channel is already installed and configured, this may already be in place — just verify it's using the correct conversion ID (`AW-17196166864`).

## Reference Values

| Field | Value |
|---|---|
| Google Ads Account ID | `AW-17196166864` |
| Purchase Conversion Label | `m7fUCO3BxNkaENDd4odA` |
| Full send_to | `AW-17196166864/m7fUCO3BxNkaENDd4odA` |
| Advertorial domain | `trustedselections.org` |
| Advertorial landing page | `/top-5-best-magnesium-2026` |
| Shopify domain | (confirm with team — likely `evolancewellness.com`) |
| Google Ads Customer ID | `243-652-1562` |

## How to Verify It's Working

After implementing all 3 tasks:

1. Open Chrome in Incognito mode
2. Install the [Google Tag Assistant](https://tagassistant.google.com/) Chrome extension
3. Navigate to `trustedselections.org/top-5-best-magnesium-2026?gclid=test123`
4. Verify the Google Ads tag (`AW-17196166864`) fires on the page
5. Click through to the Shopify store from the advertorial
6. Check that the URL now contains `_gl=` parameter (cross-domain linker working)
7. Complete a test purchase on Shopify
8. Verify the Purchase conversion event fires on the thank-you page (visible in Tag Assistant)
9. Wait 24 hours, then check Google Ads → Conversions → "Purchase" for the test conversion

## Notes

- The advertorial links to Shopify must be standard `<a href>` links (not JavaScript redirects or iframes) for the cross-domain linker to work automatically
- If links use JavaScript navigation (e.g., `window.location`), you'll need to manually decorate them. See: https://developers.google.com/tag-platform/gtagjs/configure#linker
- UTM parameters already on the links (`?utm_source=google&utm_medium=cpc&...`) will be preserved — the `_gl` parameter is added alongside them
