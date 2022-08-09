from multiprocessing import cpu_count

# Socket Path
bind = 'unix:/home/viktor-shved/fastapi_demo/gunicorn.sock'

# Worker Options
workers = cpu_count() + 1
worker_class = 'uvicorn.workers.UvicornWorker'

# Logging Options
loglevel = 'debug'
accesslog = '/home/viktor-shved/fastapi_demo/access_log'
errorlog = '/home/viktor-shved/fastapi_demo/error_log'
