import os
import sys
import argparse
import logging
from typing import List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

import config
from models import BusinessDetail
from utils import save_listings

# Configure log level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CrawlerOrchestrator")
console = Console()

# Import crawlers dynamically
from crawlers.yellowpages import YellowpagesCrawler
from crawlers.yelp import YelpCrawler
from crawlers.justdial import JustdialCrawler
from crawlers.indiamart import IndiamartCrawler
from crawlers.tradeindia import TradeindiaCrawler

CRAWLER_MAP = {
    "justdial": JustdialCrawler,
    "indiamart": IndiamartCrawler,
    "tradeindia": TradeindiaCrawler,
    "yellowpages": YellowpagesCrawler,
    "yelp": YelpCrawler
}

def parse_args():
    parser = argparse.ArgumentParser(description="Multi-Directory Business Listing Crawler")
    
    parser.add_argument(
        "--sites", 
        nargs="+", 
        choices=list(CRAWLER_MAP.keys()), 
        default=list(CRAWLER_MAP.keys()),
        help="Target websites to crawl (default: all)"
    )
    
    parser.add_argument(
        "--cities", 
        nargs="+", 
        default=config.CITIES,
        help="Cities to crawl (default: all config cities)"
    )
    
    parser.add_argument(
        "--categories", 
        nargs="+", 
        default=config.CATEGORIES,
        help="Categories to crawl (default: all config categories)"
    )
    
    parser.add_argument(
        "--output-name",
        type=str,
        default="business_listings",
        help="Output filename (without extension)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=config.MAX_RESULTS_PER_SEARCH,
        help="Maximum results to parse per search combination"
    )
    
    return parser.parse_args()

def print_welcome_banner(sites, cities, categories):
    grid = Table.grid(expand=True)
    grid.add_column(justify="center")
    grid.add_row("[bold magenta]================================================[/bold magenta]")
    grid.add_row("[bold white]   PREMIUM BUSINESS DIRECTORY CRAWLER SYSTEM    [/bold white]")
    grid.add_row("[bold magenta]================================================[/bold magenta]")
    console.print(grid)
    
    table = Table(title="Crawling Specifications", show_header=True, header_style="bold cyan")
    table.add_column("Parameter", style="dim")
    table.add_column("Selection / Count")
    
    table.add_row("Target Directories", ", ".join(sites))
    table.add_row("Cities Count", f"{len(cities)} ({', '.join(cities[:3])}...)")
    table.add_row("Categories Count", f"{len(categories)} ({categories[0]}...)")
    table.add_row("Total Crawl Combos", f"{len(sites) * len(cities) * len(categories)}")
    
    console.print(table)
    console.print("\n[yellow]Starting Crawl Engine...[/yellow]\n")

def main():
    args = parse_args()
    
    # Apply limit override if specified
    config.MAX_RESULTS_PER_SEARCH = args.limit
    
    sites = args.sites
    cities = args.cities
    categories = args.categories
    
    print_welcome_banner(sites, cities, categories)
    
    all_listings: List[BusinessDetail] = []
    
    # Set up rich progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        # Calculate total tasks
        total_steps = len(sites) * len(cities) * len(categories)
        overall_task = progress.add_task("[green]Overall Crawl Progress", total=total_steps)
        
        for site in sites:
            crawler_cls = CRAWLER_MAP.get(site)
            if not crawler_cls:
                logger.error(f"Unknown crawler: {site}")
                continue
                
            for city in cities:
                for category in categories:
                    step_desc = f"[cyan]{site.upper()}[/cyan] | {city} | {category}"
                    progress.update(overall_task, description=f"Crawling {step_desc}")
                    
                    logger.info(f"Running crawl for Site: {site}, City: {city}, Category: {category}")
                    
                    try:
                        # Instantiate and run crawler
                        crawler = crawler_cls(city=city, category=category)
                        results = crawler.run()
                        
                        if results:
                            all_listings.extend(results)
                            logger.info(f"Retrieved {len(results)} listings from {step_desc}")
                            
                            # Save intermediate results so data isn't lost if run is interrupted
                            save_listings(all_listings, filename=args.output_name)
                        else:
                            logger.info(f"No listings found for {step_desc}")
                            
                    except Exception as e:
                        logger.error(f"Error executing crawl for {step_desc}: {e}")
                        
                    progress.advance(overall_task)
                    
    console.print("\n[bold green]✔ Crawl Process Completed successfully![/bold green]")
    console.print(f"Total Listings Collected: [bold cyan]{len(all_listings)}[/bold cyan]")
    
    # Save final structured outputs
    if all_listings:
        save_listings(all_listings, filename=args.output_name)
    else:
        console.print("[yellow]Warning: No listings were extracted during this run.[/yellow]")

if __name__ == "__main__":
    main()
