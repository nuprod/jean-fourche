import logging

_logger = logging.getLogger(__name__)


def post_load():
    """
    Extend the Shopify connector (integration_shopify) so that order line custom
    attributes ("line item properties" in Shopify's terminology -- free-form key/value
    text pairs set on a line item at cart/checkout time, e.g. a gift message or an
    engraving note) are fetched in the same GraphQL request as the order, without
    modifying the vendor module's source files.

    Note: Shopify's `LineItem` type does NOT implement the `HasMetafields` interface --
    real typed/defined metafields cannot be attached to an order line item at all
    (confirmed against the live API: "Field 'metafields' doesn't exist on type
    'LineItem'"). `customAttributes` is the closest -- and only -- per-line-item data
    Shopify actually exposes for this use case.

    GraphQL body constants (GraphQLTemplate.*) and resource classes (LineItem,
    OrderLineItem, Order) are plain Python objects, not Odoo models, so they can't
    be extended with `_inherit`. They are patched here instead, once, when this
    addon's code is loaded.
    """
    from odoo.addons.integration_shopify.shopify.graphql_templates import GraphQLTemplate
    from odoo.addons.integration_shopify.shopify.resources.line_item import LineItem, OrderLineItem
    from odoo.addons.integration_shopify.shopify.resources.order import Order

    old_line_item_body = GraphQLTemplate.LINE_ITEM_BODY

    if 'customAttributes' in old_line_item_body:
        # Already patched (e.g. module reloaded in the same process).
        return

    old_order_body = GraphQLTemplate.ORDER_BODY

    custom_attributes_snippet = """
        customAttributes {
            %s
        }
    """ % GraphQLTemplate.ORDER_CUSTOM_ATTRIBUTE_BODY

    new_line_item_body = old_line_item_body + custom_attributes_snippet
    new_order_body = old_order_body.replace(old_line_item_body, new_line_item_body)

    if new_order_body == old_order_body:
        _logger.error(
            'Could not patch the Shopify ORDER_BODY GraphQL query to include line item '
            'custom attributes: LINE_ITEM_BODY was not found inside ORDER_BODY. The '
            'integration_shopify module may have changed in a way that is incompatible '
            'with this patch.'
        )
        return

    # 1. Patch the GraphQL query bodies (Order._body / LineItem._body are plain strings
    # baked in at class-definition time in integration_shopify, so the template
    # constants alone are not enough -- the resource classes must be patched too).
    GraphQLTemplate.LINE_ITEM_BODY = new_line_item_body
    GraphQLTemplate.ORDER_BODY = new_order_body
    LineItem._body = new_line_item_body
    Order._body = new_order_body

    # 2. Expose `.custom_attributes` on line items, same pattern already used by
    # integration_shopify for the order-level custom attributes (Order.custom_attributes).
    def custom_attributes(self):
        self.ensure_one()
        return {x['key']: x['value'] for x in (self['customAttributes'] or [])}

    LineItem.custom_attributes = property(custom_attributes)

    # 3. Carry the custom attributes through to the parsed order line data.
    original_parse = OrderLineItem.parse

    def parse_with_custom_attributes(self, requested_quantity):
        result = original_parse(self, requested_quantity)
        result['custom_attributes'] = self.custom_attributes
        return result

    OrderLineItem.parse = parse_with_custom_attributes

    _logger.info(
        'Shopify connector patched: order line custom attributes are now fetched with orders.'
    )
