import dotenv
from common.blob_store import BlobStore
from common.env_context import Env
from common.table_store import TableStore
from common.queue_store import QueueStore
from common.share_client import FShareService

def initialize_environment():
    dotenv.load_dotenv()
    Env.initialize()
    TableStore.initialize(Env.AZURE_STORAGETABLE_CONNECTIONSTRING)
    QueueStore.initialize(Env.AZURE_STORAGETABLE_CONNECTIONSTRING)
    FShareService.initialize(Env.AZURE_FILESHARE_CONNECTIONSTRING)
    BlobStore.initialize(Env.AZURE_STORAGETABLE_CONNECTIONSTRING)
