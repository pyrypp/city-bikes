import osmnx as ox
import logging

logging.basicConfig(filename="newfile.log",
                    format='%(asctime)s %(message)s',
                    filemode='a')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def router(i, G, orig, dest):
    logger.info(f"Starting process {i}")
    grouper = 6000
    routes = ox.shortest_path(G, orig[i:i+grouper], dest[i:i+grouper])
    logger.info(f"Finish process {i}")
    return {i: routes}
