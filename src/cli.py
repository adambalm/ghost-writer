"""
Ghost Writer CLI - Command-line interface for processing Supernote files
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from .utils.config import config
from .utils.database import DatabaseManager
from .utils.logging_setup import GhostWriterLogger
from .utils.ocr_providers import HybridOCR
from .utils.relationship_detector import RelationshipDetector
from .utils.concept_clustering import ConceptExtractor, ConceptClusterer
from .utils.structure_generator import StructureGenerator

console = Console()
logger = logging.getLogger(__name__)


def setup_cli_logging(debug: bool = False):
    """Setup logging for CLI with rich console output"""
    logger_config = {
        'level': 'DEBUG' if debug else 'INFO',
        'file_path': 'data/logs/ghost_writer.log',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'max_file_size': '10MB',
        'backup_count': 5
    }
    ghost_logger = GhostWriterLogger("ghost_writer_cli", logger_config)
    return ghost_logger


@click.group()
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging")
@click.option("--config-path", "-c", type=click.Path(), help="Path to config file")
@click.pass_context
def cli(ctx, debug, config_path):
    """Ghost Writer - Transform handwritten notes into structured documents"""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["config_path"] = config_path
    setup_cli_logging(debug)


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option("--format", "-f", type=click.Choice(["markdown", "pdf", "json", "all"]), 
              default="markdown", help="Output format")
@click.option("--quality", "-q", type=click.Choice(["fast", "balanced", "premium"]), 
              default="balanced", help="Processing quality mode")
@click.option("--local-only", is_flag=True, help="Use only local processing (no cloud APIs)")
@click.pass_context
def process(ctx, input_path: str, output: Optional[str], format: str, 
            quality: str, local_only: bool):
    """Process handwritten notes from files or directories"""
    
    console.print("🎯 [bold blue]Ghost Writer v2.0[/bold blue] - Processing Notes")
    console.print(f"📁 Input: {input_path}")
    
    input_path = Path(input_path)
    
    # Determine output directory
    if output:
        output_dir = Path(output)
    else:
        output_dir = input_path.parent / "ghost_writer_output"
    
    output_dir.mkdir(exist_ok=True)
    console.print(f"📤 Output: {output_dir}")
    
    # Find files to process
    files_to_process = []
    supported_extensions = {".png", ".jpg", ".jpeg", ".note", ".pdf"}
    
    if input_path.is_file():
        # Check if single file has supported extension
        if input_path.suffix.lower() in supported_extensions:
            files_to_process = [input_path]
    else:
        # Find supported file types in directory
        for ext in supported_extensions:
            files_to_process.extend(input_path.glob(f"**/*{ext}"))
    
    if not files_to_process:
        console.print("❌ [red]No supported files found![/red]")
        console.print("Supported formats: .png, .jpg, .jpeg, .note, .pdf")
        return
    
    console.print(f"📊 Found {len(files_to_process)} files to process")
    
    # Initialize processing components
    try:
        db_manager = DatabaseManager()
        
        # Configure OCR based on quality and local-only settings
        ocr_config = config.get("ocr", {})
        if local_only:
            # Override config to use only Tesseract
            ocr_config["providers"] = {
                "tesseract": ocr_config.get("providers", {}).get("tesseract", {})
            }
            ocr_config["hybrid"]["provider_priority"] = ["tesseract"]
        
        ocr_provider = HybridOCR(provider_config=ocr_config)
        relationship_detector = RelationshipDetector()
        concept_extractor = ConceptExtractor()
        concept_clusterer = ConceptClusterer()  
        structure_generator = StructureGenerator()
        
    except Exception as e:
        console.print(f"❌ [red]Failed to initialize components: {e}[/red]")
        if ctx.obj["debug"]:
            console.print_exception()
        return
    
    # Process files with progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        
        task = progress.add_task("Processing files...", total=len(files_to_process))
        
        for file_path in files_to_process:
            try:
                progress.update(task, description=f"Processing {file_path.name}...")
                
                # Process single file
                result = process_single_file(
                    file_path=file_path,
                    ocr_provider=ocr_provider,
                    relationship_detector=relationship_detector,
                    concept_extractor=concept_extractor,
                    concept_clusterer=concept_clusterer,
                    structure_generator=structure_generator,
                    db_manager=db_manager,
                    output_dir=output_dir,
                    output_format=format,
                    quality=quality
                )
                
                if result:
                    console.print(f"✅ [green]{file_path.name}[/green] → {result}")
                else:
                    console.print(f"❌ [red]Failed to process {file_path.name}[/red]")
                
            except Exception as e:
                console.print(f"❌ [red]Error processing {file_path.name}: {e}[/red]")
                if ctx.obj["debug"]:
                    logger.exception(f"Error processing {file_path}")
            
            progress.update(task, advance=1)
    
    console.print("🎉 [bold green]Processing complete![/bold green]")
    console.print(f"📁 Results saved to: {output_dir}")


def process_single_file(
    file_path: Path,
    ocr_provider: HybridOCR,
    relationship_detector: RelationshipDetector,
    concept_extractor: ConceptExtractor,
    concept_clusterer: ConceptClusterer,
    structure_generator: StructureGenerator,
    db_manager: DatabaseManager,
    output_dir: Path,
    output_format: str,
    quality: str
) -> Optional[str]:
    """Process a single file through the complete pipeline"""
    
    # Step 1: OCR Processing
    if file_path.suffix.lower() == ".note":
        # Convert .note file to images using enhanced clean room decoder
        from .utils.supernote_parser_enhanced import convert_note_to_images
        
        temp_dir = output_dir / "temp_images"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Use enhanced clean room decoder for pixel extraction
            image_paths = convert_note_to_images(file_path, temp_dir)
            
            if not image_paths:
                logger.warning(f"No images extracted from {file_path}")
                return None
            
            logger.info(f"Enhanced decoder extracted {len(image_paths)} pages from {file_path.name}")
            
            # Process all images and combine results
            all_text_results = []
            for i, img_path in enumerate(image_paths, 1):
                logger.info(f"Processing page {i}: {img_path.name}")
                page_result = ocr_provider.extract_text(str(img_path))
                if page_result and page_result.text.strip():
                    all_text_results.append(f"=== Page {i} ===\n{page_result.text}")
            
            if all_text_results:
                # Create combined OCR result
                combined_text = "\n\n".join(all_text_results)
                ocr_result = type(ocr_provider.extract_text(str(image_paths[0])))
                ocr_result.text = combined_text
                ocr_result.provider = f"{ocr_result.provider} (Enhanced Clean Room Decoder)"
                logger.info(f"Combined OCR result: {len(combined_text)} characters from {len(all_text_results)} pages")
            else:
                ocr_result = None
            
            # Clean up temp images
            for img_path in image_paths:
                try:
                    img_path.unlink()
                except Exception:
                    pass
            temp_dir.rmdir() if temp_dir.exists() and not list(temp_dir.iterdir()) else None
            
        except Exception as e:
            logger.error(f"Failed to process .note file {file_path}: {e}")
            return None
    else:
        # Image processing
        ocr_result = ocr_provider.extract_text(str(file_path))
    
    if not ocr_result or not ocr_result.text.strip():
        logger.warning(f"No text extracted from {file_path}")
        return None
    
    # Step 2: Store in database
    db_manager.store_note(
        source_file=str(file_path),
        raw_text=ocr_result.text,
        clean_text=ocr_result.text,
        ocr_provider=ocr_result.provider,
        ocr_confidence=ocr_result.confidence,
        processing_cost=ocr_result.cost
    )
    
    # Step 3: Create note elements for further processing
    elements = create_note_elements_from_ocr(ocr_result)
    
    # Step 4: Detect relationships
    relationships = relationship_detector.detect_relationships(elements)
    
    # Step 5: Extract and cluster concepts
    concepts = concept_extractor.extract_concepts(elements)
    clusters = concept_clusterer.cluster_concepts(concepts, relationships)
    
    # Step 6: Generate structures
    structures = structure_generator.generate_structures(
        elements, concepts, clusters, relationships
    )
    
    # Step 7: Export in requested format(s)
    output_files = []
    
    if output_format in ["markdown", "all"]:
        output_file = export_as_markdown(
            file_path, structures, output_dir, ocr_result
        )
        if output_file:
            output_files.append(output_file)
    
    if output_format in ["json", "all"]:
        output_file = export_as_json(
            file_path, structures, elements, concepts, clusters, 
            relationships, output_dir, ocr_result
        )
        if output_file:
            output_files.append(output_file)
    
    if output_format in ["pdf", "all"]:
        output_file = export_as_pdf(
            file_path, structures, output_dir, ocr_result
        )
        if output_file:
            output_files.append(output_file)
    
    return ", ".join(output_files) if output_files else None


def create_note_elements_from_ocr(ocr_result):
    """Convert OCR result to note elements for processing"""
    from .utils.relationship_detector import NoteElement
    
    # Simple implementation - split text into elements by lines
    lines = [line.strip() for line in ocr_result.text.split("\n") if line.strip()]
    
    elements = []
    for i, line in enumerate(lines):
        element = NoteElement(
            element_id=f"element_{i}",
            text=line,
            bbox=(0, i * 30, 800, (i + 1) * 30),  # Dummy bounding boxes
            confidence=ocr_result.confidence
        )
        elements.append(element)
    
    return elements


def export_as_markdown(file_path: Path, structures, output_dir: Path, ocr_result) -> Optional[str]:
    """Export processed note as Markdown"""
    
    output_file = output_dir / f"{file_path.stem}_processed.md"
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Processed Note: {file_path.name}\n\n")
            f.write(f"**Source**: {file_path}\n")
            f.write(f"**OCR Provider**: {ocr_result.provider}\n")
            f.write(f"**Confidence**: {ocr_result.confidence:.2%}\n")
            f.write(f"**Processing Cost**: ${ocr_result.cost:.4f}\n\n")
            
            f.write("## Raw Text\n\n")
            f.write(f"```\n{ocr_result.text}\n```\n\n")
            
            if structures:
                best_structure = max(structures, key=lambda s: s.confidence)
                f.write("## Structured Content\n\n")
                f.write(f"**Structure Type**: {best_structure.structure_type.value}\n")
                f.write(f"**Confidence**: {best_structure.confidence:.2%}\n\n")
                
                # Export the structured content
                structure_text = StructureGenerator().export_structure_as_text(best_structure)
                f.write(structure_text)
        
        return str(output_file.name)
    
    except Exception as e:
        logger.error(f"Failed to export markdown: {e}")
        return None


def export_as_json(file_path: Path, structures, elements, concepts, clusters, 
                   relationships, output_dir: Path, ocr_result) -> Optional[str]:
    """Export complete processing results as JSON"""
    import json
    from dataclasses import asdict
    
    output_file = output_dir / f"{file_path.stem}_data.json"
    
    try:
        # Convert dataclasses to dictionaries for JSON serialization
        data = {
            "source_file": str(file_path),
            "ocr_result": asdict(ocr_result),
            "elements": [asdict(elem) for elem in elements],
            "concepts": [asdict(concept) for concept in concepts],
            "clusters": [asdict(cluster) for cluster in clusters],
            "relationships": [asdict(rel) for rel in relationships],
            "structures": [asdict(struct) for struct in structures]
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        
        return str(output_file.name)
    
    except Exception as e:
        logger.error(f"Failed to export JSON: {e}")
        return None


def export_as_pdf(file_path: Path, structures, output_dir: Path, ocr_result) -> Optional[str]:
    """Export processed note as PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    output_file = output_dir / f"{file_path.stem}_processed.pdf"
    
    try:
        # Create PDF document
        doc = SimpleDocTemplate(str(output_file), pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph(f"Processed Note: {file_path.name}", title_style))
        story.append(Spacer(1, 12))
        
        # Metadata
        story.append(Paragraph("<b>Source:</b> " + str(file_path), styles['Normal']))
        story.append(Paragraph(f"<b>OCR Provider:</b> {ocr_result.provider}", styles['Normal']))
        story.append(Paragraph(f"<b>Confidence:</b> {ocr_result.confidence:.2%}", styles['Normal']))
        story.append(Paragraph(f"<b>Processing Cost:</b> ${ocr_result.cost:.4f}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Raw text
        story.append(Paragraph("Raw Text", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Split text into paragraphs and add to story
        for paragraph in ocr_result.text.split('\n'):
            if paragraph.strip():
                story.append(Paragraph(paragraph, styles['Normal']))
                story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 20))
        
        # Structured content
        if structures:
            best_structure = max(structures, key=lambda s: s.confidence)
            story.append(Paragraph("Structured Content", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            story.append(Paragraph(f"<b>Structure Type:</b> {best_structure.structure_type.value}", styles['Normal']))
            story.append(Paragraph(f"<b>Confidence:</b> {best_structure.confidence:.2%}", styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Export structured content
            structure_text = StructureGenerator().export_structure_as_text(best_structure)
            for paragraph in structure_text.split('\n'):
                if paragraph.strip():
                    story.append(Paragraph(paragraph, styles['Normal']))
                    story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        
        return str(output_file.name)
        
    except Exception as e:
        logger.error(f"Failed to export PDF: {e}")
        return None


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--output", "-o", type=click.Path(), help="Output directory") 
@click.option("--interval", "-i", type=int, default=5, help="Watch interval in seconds")
@click.option("--format", "-f", type=click.Choice(["markdown", "pdf", "json", "all"]), 
              default="markdown", help="Output format")
@click.pass_context  
def watch(ctx, directory: str, output: Optional[str], interval: int, format: str):
    """Watch directory for new files and process them automatically"""
    
    console.print(f"👁️  [bold blue]Watching directory:[/bold blue] {directory}")
    console.print("Press Ctrl+C to stop watching...")
    
    from .utils.file_watcher import FileWatcher
    
    directory_path = Path(directory)
    output_dir = Path(output) if output else directory_path / "ghost_writer_output"
    output_dir.mkdir(exist_ok=True)
    
    def on_file_added(file_path: Path):
        console.print(f"📄 New file detected: {file_path.name}")
        try:
            # Initialize components
            from .utils.ocr_providers import HybridOCR
            from .utils.relationship_detector import RelationshipDetector
            from .utils.concept_clustering import ConceptExtractor, ConceptClusterer
            from .utils.structure_generator import StructureGenerator
            from .utils.database import DatabaseManager
            
            ocr_provider = HybridOCR()
            detector = RelationshipDetector()
            extractor = ConceptExtractor()
            clusterer = ConceptClusterer()
            generator = StructureGenerator()
            db_manager = DatabaseManager()
            
            # Process the file
            result = process_single_file(
                file_path=file_path,
                ocr_provider=ocr_provider,
                relationship_detector=detector,
                concept_extractor=extractor,
                concept_clusterer=clusterer,
                structure_generator=generator,
                db_manager=db_manager,
                output_dir=output_dir,
                output_format=format,
                quality="balanced"
            )
            console.print(f"✅ Processed: {file_path.name} -> {result}")
        except Exception as e:
            console.print(f"❌ Error processing {file_path.name}: {e}")
    
    watcher = FileWatcher(directory_path, on_file_added, interval)
    
    try:
        watcher.start()
    except KeyboardInterrupt:
        console.print("\n🛑 [yellow]Stopping file watcher...[/yellow]")
        watcher.stop()


@cli.command()
def status():
    """Show system status and configuration"""
    
    console.print("🤖 [bold blue]Ghost Writer v2.0 - System Status[/bold blue]\n")
    
    # System info table
    table = Table(title="System Information")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")  
    table.add_column("Details", style="white")
    
    # Check database
    try:
        db_manager = DatabaseManager()
        note_count = len(db_manager.get_all_notes())
        table.add_row("Database", "✅ Connected", f"Notes: {note_count}")
    except Exception as e:
        table.add_row("Database", "❌ Error", str(e))
    
    # Check OCR providers
    try:
        ocr_config = config.get("ocr", {})
        ocr = HybridOCR(provider_config=ocr_config)
        available_providers = list(ocr.providers.keys())
        table.add_row("OCR Providers", "✅ Ready", ", ".join(available_providers))
    except Exception as e:
        table.add_row("OCR Providers", "❌ Error", str(e))
    
    # Check configuration
    try:
        config_path = config.get("database", {}).get("path", "Unknown")
        table.add_row("Configuration", "✅ Loaded", f"DB: {config_path}")
    except Exception as e:
        table.add_row("Configuration", "❌ Error", str(e))
    
    console.print(table)
    
    # Cost tracking info
    console.print("\n💰 [bold]Cost Tracking[/bold]")
    daily_limit = config.get("ocr", {}).get("hybrid", {}).get("cost_limit_per_day", 5.0)
    console.print(f"Daily Budget: ${daily_limit:.2f}")


@cli.command()
@click.option("--since", "-s", help="Sync files modified since (YYYY-MM-DD)")
@click.option("--output", "-o", type=click.Path(), help="Local directory for synced files")
@click.pass_context
def sync(ctx, since: Optional[str], output: Optional[str]):
    """Sync notes from Supernote Cloud"""
    
    console.print("☁️  [bold blue]Syncing from Supernote Cloud...[/bold blue]")
    
    from .utils.supernote_api import create_supernote_client
    from datetime import datetime
    
    # Create API client
    try:
        client = create_supernote_client(config)
        if not client:
            console.print("❌ [red]Supernote Cloud not configured[/red]")
            console.print("💡 Let's set up your Supernote credentials")
            
            # Prompt for credentials
            email = click.prompt("Enter your Supernote email", type=str)
            password = click.prompt("Enter your Supernote password", hide_input=True, type=str)
            
            # Try again with credentials (pass them directly, not via config)
            client = create_supernote_client(config, email=email, password=password)
            if not client:
                console.print("❌ [red]Authentication failed. Please check your credentials[/red]")
                return
            console.print("✅ [green]Successfully connected to Supernote Cloud![/green]")
    except Exception as e:
        console.print(f"❌ [red]Failed to initialize Supernote client: {e}[/red]")
        return
    
    # Parse since date
    since_date = None
    if since:
        try:
            since_date = datetime.fromisoformat(since)
        except ValueError:
            console.print(f"❌ [red]Invalid date format: {since}. Use YYYY-MM-DD[/red]")
            return
    
    # Determine output directory
    if output:
        sync_dir = Path(output)
    else:
        sync_dir = Path("data/supernote_sync")
    
    sync_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"📁 Sync directory: {sync_dir}")
    
    # Sync files
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            progress.add_task("Syncing files from cloud...", total=None)
            downloaded_files = client.sync_recent_files(sync_dir, since_date)
        
        if downloaded_files:
            console.print(f"✅ [green]Downloaded {len(downloaded_files)} files[/green]")
            
            # Ask if user wants to process the downloaded files
            process_now = click.confirm("Process downloaded files now?", default=True)
            
            if process_now:
                console.print("\n🔄 [blue]Processing downloaded files...[/blue]")
                
                # Use the process command logic for each downloaded file
                for file_path in downloaded_files:
                    ctx.invoke(process, 
                               input_path=str(file_path), 
                               output=str(sync_dir / "processed"),
                               format="markdown")
        else:
            console.print("ℹ️  [yellow]No new files to sync[/yellow]")
            
    except Exception as e:
        console.print(f"❌ [red]Sync failed: {e}[/red]")
        if ctx.obj["debug"]:
            console.print_exception()


@cli.command()
def init():
    """Initialize Ghost Writer configuration and database"""
    
    console.print("🚀 [bold blue]Initializing Ghost Writer...[/bold blue]")
    
    try:
        # Create data directories
        data_dirs = ["data/database", "data/notes", "data/faiss_index", "data/logs"]
        for dir_path in data_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            console.print(f"📁 Created directory: {dir_path}")
        
        # Initialize database
        DatabaseManager()
        console.print("✅ Database initialized")
        
        # Test OCR providers
        ocr_config = config.get("ocr", {})
        ocr = HybridOCR(provider_config=ocr_config)
        console.print(f"✅ OCR providers ready: {', '.join(ocr.providers.keys())}")
        
        console.print("\n🎉 [bold green]Ghost Writer initialized successfully![/bold green]")
        console.print("🏃 Ready to process notes with: [bold]ghost-writer process <path>[/bold]")
        
    except Exception as e:
        console.print(f"❌ [red]Initialization failed: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point for the CLI"""
    cli()


if __name__ == "__main__":
    main()