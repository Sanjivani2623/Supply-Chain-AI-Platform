# Import every model so Base.metadata knows about all tables (used by create_all / Alembic).
from app.models.user import User
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.sales import Sale
from app.models.purchase_order import PurchaseOrder
from app.models.news_article import NewsArticle
from app.models.disruption_event import DisruptionEvent
from app.models.disruption_prediction import DisruptionPrediction
from app.models.forecast import Forecast
from app.models.inventory_recommendation import InventoryRecommendation
from app.models.alert import Alert
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.conversation import Conversation, Message, Citation
from app.models.audit_log import AuditLog
