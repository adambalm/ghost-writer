# PROJECT MAP - Ghost Writer System Architecture

## DEPLOYMENT CONFIGURATION [verified]
- **Production URL**: http://100.111.114.84:5000 [verified source:archive/experimental/get_my_note.py:201]
- **Local Development**: http://localhost:5000 [verified source:archive/experimental/web_viewer.py:582] 
- **Flask Configuration**: host='0.0.0.0', port=5000, debug=True [verified source:archive/experimental/web_viewer.py:587]

## WORKING SYSTEM COMPONENTS (as of 2025-08-18) [verified]

### Web Interface
- **Primary**: archive/experimental/web_viewer.py [verified source:file exists]
- **Enhanced**: enhanced_web_viewer.py (port 5001) [verified source:file exists]
- **Entry Point**: Flask app with sn2md integration [verified source:archive/experimental/web_viewer.py:19]

### Extraction Pipeline [verified]
- **Working Method**: sn2md + supernotelib [verified source:parallel_test_results.json:3-4]
- **Success Visibility**: VisibilityOverlay.INVISIBLE [verified source:parallel_test_results.json:9]
- **Performance**: 2,859,430 pixels page 1, 2,693,922 pixels page 2 [verified source:parallel_test_results.json:10,22]

### OCR & Transcription [verified]
- **Provider**: GPT-4o Vision API [verified source:transcription_gpt_4o_vision.txt:1]
- **Success Rate**: 95% confidence [verified source:transcription_gpt_4o_vision.txt:2]
- **Cost**: $0.0109 per transcription [verified source:transcription_gpt_4o_vision.txt:3]

## DATA FLOWS [verified]

### Supernote Processing Flow
1. **File Upload/Selection** → Web Interface (port 5000)
2. **sn2md Import** → load_notebook() [verified source:archive/experimental/web_viewer.py:34]
3. **Conversion** → ImageConverter + VisibilityOverlay [verified source:archive/experimental/web_viewer.py:35-36]
4. **Extraction** → PNG images with 2.8M+ pixels [verified source:parallel_test_results.json]
5. **OCR** → GPT-4o Vision transcription [verified source:transcription_gpt_4o_vision.txt]

### File Locations [verified]
- **Results Directory**: /home/ed/ghost-writer/results/ [verified source:archive/experimental/web_viewer.py:23]
- **Upload Directory**: /home/ed/ghost-writer/uploads/ [verified source:archive/experimental/web_viewer.py:22]
- **Project Root**: /home/ed/ghost-writer [verified source:archive/experimental/web_viewer.py:15]

## ENVIRONMENT VARIABLES [inference]
- **OPENAI_API_KEY**: Required for GPT-4o Vision [inference from transcription evidence]
- **Flask Environment**: Debug mode enabled [verified source:archive/experimental/web_viewer.py:587]

## FORBIDDEN DEPENDENCIES [verified]
- **sn2md**: 278 references found [verified source:rg count]
- **supernotelib**: Used by working system but AGPL licensed [verified source:multiple files]
- **Status**: All sn2md/supernotelib code must be quarantined [verified requirement]

## SUBAGENTS/MCP SERVERS [inference]
- **No Evidence Found**: No playwright, MCP server, or browser automation detected [verified source:comprehensive search]
- **Visual Inspection**: Manual browser testing at 100.111.114.84:5000 [inference from evidence]

## ARCHIVE IMPACT [verified]
- **Moved Files**: Critical working components in archive/experimental/ [verified source:file locations]
- **Date**: Archive created 2025-08-19 00:46 after working state [verified source:ls timestamps]
- **Recovery Needed**: Restore working web_viewer.py without sn2md [inference]

## CURRENT VS WORKING STATE [verified]
- **Current**: enhanced_web_viewer.py (port 5001) with clean room decoder [verified source:file exists]
- **Working**: archive/experimental/web_viewer.py (port 5000) with sn2md [verified source:evidence]
- **Gap**: Clean room decoder extracts 0 strokes vs sn2md 2.8M pixels [verified from test results]