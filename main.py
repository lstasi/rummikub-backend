#!/usr/bin/env python3
"""
Main entry point for Rummikub Backend API.
This file maintains backward compatibility by importing from the src module.
"""

if __name__ == "__main__":
    import uvicorn
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Rummikub Backend API server...")
    logger.info("Server will be available at: http://localhost:8090")
    logger.info("API documentation: http://localhost:8090/docs")
    
    # Import and run the app from src module
    uvicorn.run(
        "src.main:app", 
        host="0.0.0.0", 
        port=8090,
        log_level="debug",
        access_log=True,
        reload=True  # Enable auto-reload for development
    )