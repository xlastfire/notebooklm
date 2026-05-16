import asyncio
import os
from pathlib import Path
from typing import List, Optional, Any
from notebooklm import (
    NotebookLMClient, 
    RPCError, 
    SourceType, 
    ArtifactType,
    AudioFormat,
    AudioLength,
    ReportFormat,
    QuizQuantity,
    QuizDifficulty,
    GenerationStatus
)

class NotebookAgent:
    def __init__(self):
        self.client: Optional[NotebookLMClient] = None
        self.current_nb_id: Optional[str] = None
        self.current_nb_title: Optional[str] = "None"
        self.storage_path: str = ""
        self.notifications: List[str] = []
        self.active_tasks_count: int = 0
        
    async def connect(self, storage_path: str):
        """Connect to NotebookLM using a specific storage file."""
        if self.client:
            await self.client.__aexit__(None, None, None)
            
        self.storage_path = os.path.abspath(storage_path)
        # Set environment variable so the library's internal CLI calls use this path
        os.environ["NOTEBOOKLM_STORAGE_PATH"] = self.storage_path
        
        try:
            self.client = await NotebookLMClient.from_storage(self.storage_path, keepalive=600)
            await self.client.__aenter__()
            return True
        except Exception:
            return False

    async def disconnect(self):
        if self.client:
            await self.client.__aexit__(None, None, None)
            self.client = None

    async def list_notebooks(self):
        if not self.client: return []
        return await self.client.notebooks.list()

    async def create_notebook(self, title: str):
        if not self.client: return None
        nb = await self.client.notebooks.create(title)
        self.current_nb_id = nb.id
        self.current_nb_title = nb.title
        return nb

    async def delete_notebook(self, nb_id: str):
        if not self.client: return False
        success = await self.client.notebooks.delete(nb_id)
        if success and nb_id == self.current_nb_id:
            self.current_nb_id = None
            self.current_nb_title = "None"
        return success

    async def add_source(self, type: str, value: str, title: Optional[str] = None, wait: bool = True):
        if not self.client or not self.current_nb_id: return None
        if type == "url":
            return await self.client.sources.add_url(self.current_nb_id, value, wait=wait)
        elif type == "file":
            return await self.client.sources.add_file(self.current_nb_id, Path(value), title=title, wait=wait)
        elif type == "text":
            return await self.client.sources.add_text(self.current_nb_id, title or "Pasted Text", value, wait=wait)
        return None

    async def add_source_bg(self, type: str, value: str, title: Optional[str] = None):
        if not self.client or not self.current_nb_id: return
        nb_id = self.current_nb_id
        self.active_tasks_count += 1
        try:
            res = await self.add_source(type, value, title, wait=True)
            if res:
                self.notifications.append(f"✅ Source added & indexed: {title or value}")
            else:
                self.notifications.append(f"❌ Failed to add source: {title or value}")
        except Exception as e:
            self.notifications.append(f"❌ Source error ({title or value}): {str(e)}")
        finally:
            self.active_tasks_count -= 1

    async def list_sources(self):
        if not self.client or not self.current_nb_id: return []
        return await self.client.sources.list(self.current_nb_id)

    async def delete_source(self, source_id: str):
        if not self.client or not self.current_nb_id: return False
        return await self.client.sources.delete(self.current_nb_id, source_id)

    async def chat(self, query: str, conversation_id: Optional[str] = None):
        if not self.client or not self.current_nb_id: return None
        return await self.client.chat.ask(self.current_nb_id, query, conversation_id=conversation_id)

    async def generate_artifact(self, art_type: str, instructions: str = "", language: str = "English"):
        if not self.client or not self.current_nb_id: return None
        nb_id = self.current_nb_id
        
        # Combine language and instructions
        full_instr = f"Language: {language}. "
        if instructions:
            full_instr += instructions
            
        if art_type == "audio":
            return await self.client.artifacts.generate_audio(nb_id, instructions=full_instr)
        elif art_type == "video":
            return await self.client.artifacts.generate_video(nb_id, instructions=full_instr)
        elif art_type == "quiz":
            return await self.client.artifacts.generate_quiz(nb_id, instructions=full_instr)
        elif art_type == "flashcards":
            return await self.client.artifacts.generate_flashcards(nb_id, instructions=full_instr)
        elif art_type == "blog_post":
            return await self.client.artifacts.generate_report(nb_id, report_format=ReportFormat.BLOG_POST, extra_instructions=full_instr)
        elif art_type == "mind_map":
            return await self.client.artifacts.generate_mind_map(nb_id)
        elif art_type == "briefing_doc":
            return await self.client.artifacts.generate_report(nb_id, report_format=ReportFormat.BRIEFING_DOC, extra_instructions=full_instr)
        elif art_type == "study_guide":
            return await self.client.artifacts.generate_report(nb_id, report_format=ReportFormat.STUDY_GUIDE, extra_instructions=full_instr)
        elif art_type == "slide_deck":
            return await self.client.artifacts.generate_slide_deck(nb_id)
        elif art_type == "infographic":
            return await self.client.artifacts.generate_infographic(nb_id)
        elif art_type == "data_table":
            return await self.client.artifacts.generate_data_table(nb_id)
        return None

    async def generate_artifact_bg(self, art_type: str, instructions: str = "", language: str = "English"):
        if not self.client or not self.current_nb_id: return
        nb_id = self.current_nb_id
        self.active_tasks_count += 1
        try:
            status = await self.generate_artifact(art_type, instructions, language=language)
            if not status:
                self.notifications.append(f"❌ Failed to start {art_type} generation")
                return
            
            # Wait for completion
            res = await self.wait_for_artifact(status.task_id)
            if res and res.status == GenerationStatus.COMPLETED:
                self.notifications.append(f"✅ Artifact ready ({language}): {art_type} ({status.task_id})")
            else:
                self.notifications.append(f"❌ Artifact generation failed ({language}): {art_type}")
        except Exception as e:
            self.notifications.append(f"❌ Artifact error ({art_type}): {str(e)}")
        finally:
            self.active_tasks_count -= 1


    async def wait_for_artifact(self, task_id: str):
        if not self.client or not self.current_nb_id: return None
        return await self.client.artifacts.wait_for_completion(self.current_nb_id, task_id)

    async def download_artifact(self, art_id: str, art_kind: str, output_name: Optional[str] = None):
        if not self.client or not self.current_nb_id: return None
        nb_id = self.current_nb_id
        name = output_name or f"downloaded_{art_id}"
        if art_kind == "audio":
            return await self.client.artifacts.download_audio(nb_id, f"{name}.mp3", artifact_id=art_id)
        elif art_kind == "video":
            return await self.client.artifacts.download_video(nb_id, f"{name}.mp4", artifact_id=art_id)
        elif art_kind == "quiz":
            return await self.client.artifacts.download_quiz(nb_id, f"{name}.json", artifact_id=art_id)
        elif art_kind == "flashcards":
            return await self.client.artifacts.download_flashcards(nb_id, f"{name}.json", artifact_id=art_id)
        elif art_kind == "mind_map":
            return await self.client.artifacts.download_mind_map(nb_id, f"{name}.json", artifact_id=art_id)
        elif art_kind == "report":
            return await self.client.artifacts.download_report(nb_id, f"{name}.md", artifact_id=art_id)
        elif art_kind == "slide_deck":
            return await self.client.artifacts.download_slide_deck(nb_id, f"{name}.pdf", artifact_id=art_id)
        elif art_kind == "infographic":
            return await self.client.artifacts.download_infographic(nb_id, f"{name}.png", artifact_id=art_id)
        elif art_kind == "data_table":
            return await self.client.artifacts.download_data_table(nb_id, f"{name}.csv", artifact_id=art_id)
        return None

    async def download_artifact_bg(self, art_id: str, art_kind: str, title: str):
        self.active_tasks_count += 1
        try:
            # Automatically wait if it's still generating
            await self.wait_for_artifact(art_id)
            
            path = await self.download_artifact(art_id, art_kind, title.replace(" ","_"))
            if path:
                self.notifications.append(f"📥 Download complete: {title} -> {path}")
            else:
                self.notifications.append(f"❌ Download failed: {title}")
        except Exception as e:
            self.notifications.append(f"❌ Download error ({title}): {str(e)}")
        finally:
            self.active_tasks_count -= 1

    async def research_auto(self, query: str, deep: bool = False):
        if not self.client or not self.current_nb_id: return None
        nb_id = self.current_nb_id  # Snapshot NB ID for background safety
        self.active_tasks_count += 1
        try:
            mode = "deep" if deep else "fast"
            task = await self.client.research.start(nb_id, query, mode=mode)
            if not task: 
                self.notifications.append(f"❌ Research failed to start: {query}")
                return None
            
            task_id = task["task_id"]
            while True:
                status = await self.client.research.poll(nb_id)
                if status["status"] == "completed":
                    break
                await asyncio.sleep(5)
                
            sources = status.get("sources", [])
            if sources:
                await self.client.research.import_sources(nb_id, task_id, sources)
                self.notifications.append(f"✅ Research completed & imported: {query}")
                return True
            self.notifications.append(f"⚠️ Research completed but found no sources: {query}")
            return False
        except Exception as e:
            self.notifications.append(f"❌ Research error ({query}): {str(e)}")
            return False
        finally:
            self.active_tasks_count -= 1

    async def auto_pilot_bg(self, topic: str, language: str = "English"):
        self.active_tasks_count += 1
        try:
            # 1. Create NB
            nb = await self.create_notebook(f"Auto-Pilot: {topic}")
            if not nb:
                self.notifications.append(f"❌ Auto-Pilot failed: Could not create notebook for {topic}")
                return
            nb_id = nb.id
            
            # 2. Research
            mode = "fast"
            task = await self.client.research.start(nb_id, topic, mode=mode)
            if task:
                task_id = task["task_id"]
                while True:
                    status = await self.client.research.poll(nb_id)
                    if status["status"] == "completed": break
                    await asyncio.sleep(5)
                sources = status.get("sources", [])
                if sources:
                    await self.client.research.import_sources(nb_id, task_id, sources)
            
            # 3. Audio
            full_instr = f"Language: {language}."
            status = await self.client.artifacts.generate_audio(nb_id, instructions=full_instr)
            if status:
                await self.client.artifacts.wait_for_completion(nb_id, status.task_id)
                filename = f"{topic.replace(' ', '_')}_{language}_podcast.mp3"
                await self.client.artifacts.download_audio(nb_id, filename, artifact_id=status.task_id)
                self.notifications.append(f"🚀 Auto-Pilot Finished ({language})! Podcast ready: {filename}")
            else:
                self.notifications.append(f"⚠️ Auto-Pilot partially done: Research imported, but audio failed.")
        except Exception as e:
            self.notifications.append(f"❌ Auto-Pilot error ({topic}): {str(e)}")
        finally:
            self.active_tasks_count -= 1

