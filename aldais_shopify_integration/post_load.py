import logging

_logger = logging.getLogger(__name__)


def post_load():
    """
    Extend the Shopify connector (integration_shopify) so that line item metafields
    are fetched in the same GraphQL request as the order, without modifying the
    vendor module's source files.

    GraphQL body constants (GraphQLTemplate.*) and resource classes (LineItem,
    OrderLineItem, Order) are plain Python objects, not Odoo models, so they can't
    be extended with `_inherit`. They are patched here instead, once, when this
    addon's code is loaded.
    """
    from odoo.addons.integration_shopify.shopify.graphql_templates import GraphQLTemplate
    from odoo.addons.integration_shopify.shopify.resources.line_item import LineItem, OrderLineItem
    from odoo.addons.integration_shopify.shopify.resources.metafields_mixin import MetafieldMixin
    from odoo.addons.integration_shopify.shopify.resources.order import Order

    old_line_item_body = GraphQLTemplate.LINE_ITEM_BODY

    if 'metafields(' in old_line_item_body:
        # Already patched (e.g. module reloaded in the same process).
        return

    old_order_body = GraphQLTemplate.ORDER_BODY

    metafields_snippet = """
        metafields(first: 50) {
            nodes {
                %s
            }
        }
    """ % GraphQLTemplate.METAFIELD_BODY

    new_line_item_body = old_line_item_body + metafields_snippet
    new_order_body = old_order_body.replace(old_line_item_body, new_line_item_body)

    if new_order_body == old_order_body:
        _logger.error(
            'Could not patch the Shopify ORDER_BODY GraphQL query to include line item '
            'metafields: LINE_ITEM_BODY was not found inside ORDER_BODY. The integration_shopify '
            'module may have changed in a way that is incompatible with this patch.'
        )
        return

    # 1. Patch the GraphQL query bodies (Order._body / LineItem._body are plain strings
    # baked in at class-definition time in integration_shopify, so the template
    # constants alone are not enough -- the resource classes must be patched too).
    GraphQLTemplate.LINE_ITEM_BODY = new_line_item_body
    GraphQLTemplate.ORDER_BODY = new_order_body
    LineItem._body = new_line_item_body
    Order._body = new_order_body

    # 2. Expose `.metafields` / `.get_metafields()` on line items, same mechanism
    # already used by integration_shopify for Order/Customer/Product.
    LineItem.metafields = MetafieldMixin.metafields
    LineItem.get_metafields = MetafieldMixin.get_metafields
    LineItem._prepare_metafields_body = MetafieldMixin._prepare_metafields_body

    # 3. Carry the metafields through to the parsed order line data.
    original_parse = OrderLineItem.parse

    def parse_with_metafields(self, requested_quantity):
        result = original_parse(self, requested_quantity)
        result['metafields'] = [x.to_dict() for x in self.metafields]
        return result

    OrderLineItem.parse = parse_with_metafields

    _logger.info('Shopify connector patched: order line metafields are now fetched with orders.')
