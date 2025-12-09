from dataclasses import dataclass, asdict
from typing import List, Optional

@dataclass
class ProductDTO:
    """Data Transfer Object for Product"""
    id: int
    name: str
    item_no: str
    qty: int
    item_type: str
    company_id: int
    company_name: str
    active: bool

    @classmethod
    def from_model(cls, product):
        """Create DTO from Product model instance"""
        return cls(
            id=product.id,
            name=product.name,
            item_no=product.item_no,
            qty=product.qty,
            item_type=product.item_type,
            company_id=product.company.id,
            company_name=product.company.name,
            active=product.active
        )

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

@dataclass
class OrderItemDTO:
    """DTO for order line items"""
    product_id: int
    product_name: str
    item_no: str
    quantity: int
    item_type: str

    def to_dict(self):
        return asdict(self)

@dataclass
class OrderDTO:
    """Data Transfer Object for Order"""
    id: int
    date: str
    creator_id: int
    creator_username: str
    items: List[OrderItemDTO]
    total_items: int
    company_name: Optional[str] = None

    @classmethod
    def from_model(cls, order):
        """Create DTO from Order model instance"""
        product_orders = order.productorder_set.select_related(
            'product__company'
        ).all()

        items = [
            OrderItemDTO(
                product_id=po.product.id,
                product_name=po.product.name,
                item_no=po.product.item_no,
                quantity=po.quantity,
                item_type=po.product.item_type
            )
            for po in product_orders
        ]

        # Get company name from first item
        company_name = None
        if product_orders:
            company_name = product_orders[0].product.company.name

        return cls(
            id=order.id,
            date=order.date.strftime('%Y-%m-%d %H:%M'),
            creator_id=order.creator.id,
            creator_username=order.creator.username,
            items=items,
            total_items=sum(po.quantity for po in product_orders),
            company_name=company_name
        )

    def to_dict(self):
        data = asdict(self)
        # Convert nested datacl dataclasses to dicts
        data['items'] = [
            item.to_dict() if hasattr(item, 'to_dict') else item
            for item in self.items
        ]
        return data

@dataclass
class CompanyDTO:
    """Data Transfer Object for Company"""
    id: int
    name: str
    product_count: int
    created_at: str

    @classmethod
    def from_model(cls, company):
        return cls(
            id=company.id,
            name=company.name,
            product_count=company.company_products.filter(active=True).count(),
            created_at=company.created_at.strftime('%Y-%m-%d')
        )

    def to_dict(self):
        return asdict(self)