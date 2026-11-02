# Add this import to src/hr_aiaas/main.py
from hr_aiaas.api.v1 import api_v1_router

# Inside create_application(), before `return application`:
application.include_router(api_v1_router)
