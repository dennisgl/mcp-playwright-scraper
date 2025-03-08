import asyncio
import re
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

# Initialize the MCP server
server = Server("mcp-playwright-scraper")

# Resource Management
class ResourceManager:
    """
    Manages scraped web pages as resources for the session.
    Provides access to scraped content via MCP resources.
    """
    def __init__(self):
        self.resources: Dict[str, Dict] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # URI to session_ids
    
    def add_resource(self, url: str, content: str, mime_type: str) -> str:
        """
        Add a scraped web page as a resource.
        
        Args:
            url: Original URL that was scraped
            content: The scraped content
            mime_type: Content MIME type
            
        Returns:
            Resource URI
        """
        # Generate a unique identifier for this scraped page
        resource_id = str(uuid.uuid4())
        uri = f"scrape://{resource_id}"
        
        # Store the resource
        self.resources[uri] = {
            "url": url,
            "content": content,
            "mime_type": mime_type,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Notify subscribers of resource list change
        self.notify_list_changed()
        
        return uri
    
    def get_resource(self, uri: str) -> Optional[Dict]:
        """
        Get a resource by URI.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource data or None if not found
        """
        return self.resources.get(uri)
    
    def list_resources(self) -> List[Dict]:
        """
        List all available resources.
        
        Returns:
            List of resource metadata
        """
        return [
            {
                "uri": uri,
                "name": f"Scraped: {data['url']}",
                "description": f"Web page scraped on {data['timestamp']}",
                "mimeType": data["mime_type"]
            }
            for uri, data in self.resources.items()
        ]
    
    def subscribe(self, uri: str, session_id: str) -> bool:
        """
        Subscribe to updates for a resource.
        
        Args:
            uri: Resource URI
            session_id: Session ID
            
        Returns:
            True if successfully subscribed, False otherwise
        """
        if uri not in self.resources:
            return False
        
        if uri not in self.subscriptions:
            self.subscriptions[uri] = []
        
        if session_id not in self.subscriptions[uri]:
            self.subscriptions[uri].append(session_id)
        
        return True
    
    def unsubscribe(self, uri: str, session_id: str) -> bool:
        """
        Unsubscribe from updates for a resource.
        
        Args:
            uri: Resource URI
            session_id: Session ID
            
        Returns:
            True if successfully unsubscribed, False otherwise
        """
        if uri not in self.subscriptions:
            return False
        
        if session_id in self.subscriptions[uri]:
            self.subscriptions[uri].remove(session_id)
            
            # Clean up empty subscription lists
            if not self.subscriptions[uri]:
                del self.subscriptions[uri]
        
        return True
    
    def update_resource(self, uri: str, content: str, mime_type: str) -> bool:
        """
        Update an existing resource.
        
        Args:
            uri: Resource URI
            content: New content
            mime_type: New MIME type
            
        Returns:
            True if successfully updated, False otherwise
        """
        if uri not in self.resources:
            return False
        
        self.resources[uri]["content"] = content
        self.resources[uri]["mime_type"] = mime_type
        self.resources[uri]["timestamp"] = datetime.now().isoformat()
        
        # Notify subscribers of resource update
        self.notify_resource_updated(uri)
        
        return True
    
    def notify_list_changed(self):
        """
        Notify clients that the resource list has changed.
        """
        # This would be implemented if we had active sessions tracking
        pass
    
    def notify_resource_updated(self, uri: str):
        """
        Notify subscribers that a resource has been updated.
        
        Args:
            uri: Resource URI
        """
        # This would be implemented if we had active sessions tracking
        pass
    
    def cleanup(self):
        """
        Clean up all resources.
        """
        self.resources.clear()
        self.subscriptions.clear()

# Initialize resource manager
resource_manager = ResourceManager()

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available web page resources that have been scraped.
    """
    resources_list = resource_manager.list_resources()
    return [
        types.Resource(
            uri=r["uri"],
            name=r["name"],
            description=r["description"],
            mimeType=r["mimeType"]
        )
        for r in resources_list
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific scraped page's content by its URI.
    """
    uri_str = str(uri)
    
    if uri_str.startswith("scrape://"):
        resource = resource_manager.get_resource(uri_str)
        if resource:
            return resource["content"]
        else:
            raise ValueError(f"Resource not found: {uri_str}")
    else:
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

@server.subscribe_resource()
async def handle_subscribe_resource(uri: AnyUrl, session_id: str) -> None:
    """
    Subscribe to updates for a specific resource.
    """
    uri_str = str(uri)
    
    if not resource_manager.subscribe(uri_str, session_id):
        raise ValueError(f"Cannot subscribe to resource: {uri_str}")

@server.unsubscribe_resource()
async def handle_unsubscribe_resource(uri: AnyUrl, session_id: str) -> None:
    """
    Unsubscribe from updates for a specific resource.
    """
    uri_str = str(uri)
    
    if not resource_manager.unsubscribe(uri_str, session_id):
        raise ValueError(f"Cannot unsubscribe from resource: {uri_str}")

# Prompts
@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts.
    """
    return []

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate a prompt based on the scraped content.
    """
    raise ValueError(f"Unknown prompt: {name}")

# Tools
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available scraping tools.
    """
    return [
        types.Tool(
            name="scrape_to_markdown",
            description="Scrape a URL and convert the content to markdown",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to scrape"},
                    "verify_ssl": {"type": "boolean", "description": "Whether to verify SSL certificates (default: true)"}
                },
                "required": ["url"]
            }
        )
    ]

# Scraper implementation based on scrape.py
class Scraper:
    """
    Web scraper that converts HTML to Markdown using the best tools available.
    """
    pandoc_available = None
    playwright_available = None
    user_agent = "Playwright-MCP-Scraper/0.1.0"
    
    def __init__(self, verify_ssl=True, print_error=None):
        """
        Initialize the scraper.
        
        Args:
            verify_ssl: Whether to verify SSL certificates
            print_error: Function to report errors
        """
        self.verify_ssl = verify_ssl
        self.print_error = print_error if print_error else print
    
    async def scrape(self, url):
        """
        Scrape a URL and turn it into readable markdown if it's HTML.
        If it's plain text or non-HTML, return it as-is.
        
        Args:
            url: The URL to scrape
        """
        # Normalize URL
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        
        content, mime_type = await self.scrape_with_playwright(url)
        
        if not content:
            self.print_error(f"Failed to retrieve content from {url}")
            return f"# Failed to retrieve content from {url}"
        
        # Check if the content is HTML based on MIME type or content
        if (mime_type and mime_type.startswith("text/html")) or (
            mime_type is None and self.looks_like_html(content)
        ):
            await self.try_pandoc()
            markdown = await self.html_to_markdown(content)
            return markdown
        
        return f"```\n{content}\n```"
    
    def looks_like_html(self, content):
        """
        Check if the content looks like HTML.
        """
        if isinstance(content, str):
            # Check for common HTML tags
            html_patterns = [
                r"<!DOCTYPE\s+html",
                r"<html",
                r"<head",
                r"<body",
                r"<div",
                r"<p>",
                r"<a\s+href=",
            ]
            return any(re.search(pattern, content, re.IGNORECASE) for pattern in html_patterns)
        return False
    
    async def scrape_with_playwright(self, url):
        """
        Scrape a URL using Playwright.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Tuple of (content, mime_type)
        """
        from playwright.async_api import async_playwright
        
        playwright = None
        browser = None
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(ignore_https_errors=not self.verify_ssl)
            page = await context.new_page()
            
            # Set user agent
            user_agent = await page.evaluate("navigator.userAgent")
            user_agent = user_agent.replace("Headless", "")
            user_agent = user_agent.replace("headless", "")
            user_agent += " " + self.user_agent
            
            await page.set_extra_http_headers({"User-Agent": user_agent})
            
            response = None
            try:
                # Change to 'load' wait strategy and increase timeout to 30 seconds
                response = await page.goto(url, wait_until="load", timeout=30000)
            except Exception as e:
                self.print_error(f"Error navigating to {url}: {str(e)}")
                return None, None
            
            try:
                content = await page.content()
                mime_type = None
                if response:
                    content_type = await response.header_value("content-type")
                    if content_type:
                        mime_type = content_type.split(";")[0]
                return content, mime_type
            except Exception as e:
                self.print_error(f"Error retrieving page content: {str(e)}")
                return None, None
                
        except Exception as e:
            self.print_error(f"Playwright error: {str(e)}")
            return None, None
        finally:
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass
            if playwright:
                try:
                    await playwright.stop()
                except Exception:
                    pass
    
    async def try_pandoc(self):
        """
        Check if pandoc is available and try to install it if not.
        """
        if self.pandoc_available is not None:
            return self.pandoc_available
        
        try:
            import pypandoc
            try:
                pypandoc.get_pandoc_version()
                self.pandoc_available = True
                return True
            except OSError:
                pass
            
            try:
                await asyncio.to_thread(pypandoc.download_pandoc, delete_installer=True)
                self.pandoc_available = True
                return True
            except Exception as err:
                self.print_error(f"Unable to install pandoc: {err}")
                self.pandoc_available = False
                return False
                
        except ImportError:
            self.print_error("pypandoc not installed")
            self.pandoc_available = False
            return False
    
    async def html_to_markdown(self, page_source):
        """
        Convert HTML to Markdown using BeautifulSoup and pypandoc.
        
        Args:
            page_source: HTML content to convert
            
        Returns:
            Markdown content
        """
        try:
            from bs4 import BeautifulSoup
            
            # Use BeautifulSoup to clean up the HTML
            soup = BeautifulSoup(page_source, "html.parser")
            soup = await asyncio.to_thread(self.slimdown_html, soup)
            page_source = str(soup)
            
            # Check if pandoc is available
            if not self.pandoc_available:
                # Fallback to a simple conversion
                text = soup.get_text(separator="\n\n")
                title = soup.title.string if soup.title else "Scraped Content"
                return f"# {title}\n\n{text}"
            
            # Use pypandoc for conversion
            import pypandoc
            try:
                md = await asyncio.to_thread(pypandoc.convert_text, page_source, "markdown", format="html")
            except OSError:
                # Fallback if pandoc conversion fails
                text = soup.get_text(separator="\n\n")
                title = soup.title.string if soup.title else "Scraped Content"
                return f"# {title}\n\n{text}"
            
            # Clean up the markdown
            md = re.sub(r"</div>", "      ", md)
            md = re.sub(r"<div>", "     ", md)
            md = re.sub(r"\n\s*\n", "\n\n", md)
            
            return md
            
        except ImportError:
            # If BeautifulSoup is not available, return simple text extraction
            return f"# Scraped Content\n\n{page_source}"
    
    def slimdown_html(self, soup):
        """
        Clean up HTML using BeautifulSoup.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Cleaned BeautifulSoup object
        """
        # Remove SVG elements
        for svg in soup.find_all("svg"):
            svg.decompose()
        
        # Remove images
        if soup.img:
            soup.img.decompose()
        
        # Remove data URIs
        for tag in soup.find_all(href=lambda x: x and x.startswith("data:")):
            tag.decompose()
        
        for tag in soup.find_all(src=lambda x: x and x.startswith("data:")):
            tag.decompose()
        
        # Remove attributes except href
        for tag in soup.find_all(True):
            for attr in list(tag.attrs):
                if attr != "href":
                    tag.attrs.pop(attr, None)
        
        return soup

# Tool handler
@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    """
    if name == "scrape_to_markdown":
        if not arguments or "url" not in arguments:
            return [types.TextContent(type="text", text="URL is required")]
        
        url = arguments.get("url")
        verify_ssl = arguments.get("verify_ssl", True)
        
        # Create scraper instance
        scraper = Scraper(verify_ssl=verify_ssl)
        
        # Scrape the URL and convert to markdown
        markdown = await scraper.scrape(url)
        
        # Store the scraped content as a resource
        original_mime_type = "text/html"  # Default assumption
        # No need to call scrape_with_playwright again - we already have the markdown
        
        # Save as a resource
        resource_uri = resource_manager.add_resource(
            url=url,
            content=markdown,
            mime_type="text/markdown"
        )
        
        # Return the content as text only - fixing the split() error
        return [
            types.TextContent(type="text", text=markdown)
        ]
    else:
        raise ValueError(f"Unknown tool: {name}")

# Cleanup resources when server stops
async def cleanup_resources():
    """
    Clean up resources when the server stops.
    """
    resource_manager.cleanup()

# Main server function
async def main():
    try:
        # Run the server using stdin/stdout streams
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-playwright-scraper",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    finally:
        # Clean up resources when server stops
        await cleanup_resources()

if __name__ == "__main__":
    asyncio.run(main())