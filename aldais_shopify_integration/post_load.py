import logging

_logger = logging.getLogger(__name__)


def post_load():
    """
    Intended to extend the Shopify connector (integration_shopify) so that order line
    metafields are fetched in the same GraphQL request as the order, without modifying
    the vendor module's source files.

    Currently a no-op: Shopify's Admin GraphQL API does not expose a `metafields` field
    on the `LineItem` type (it does not implement the `HasMetafields` interface), so the
    GraphQL query patch this was meant to apply is invalid and would break every order
    fetch (confirmed on staging: "Field 'metafields' doesn't exist on type 'LineItem'").
    See the module's other files (sale_integration.py, integration_sale_order_factory.py,
    metafield_mapping.py, views) for the still-relevant mapping plumbing, which is
    inactive until this is revisited with the correct Shopify field
    (e.g. `customAttributes` on LineItem, or metafields on the related Product/Variant).
    """
    return
