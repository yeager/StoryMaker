"""Story Library view for downloading and managing pre-made stories."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

import json
import os
import threading
from pathlib import Path
from gi.repository import Gtk, Adw, GObject, GLib

from storymaker.models.story import Story
from storymaker.utils.i18n import _
from storymaker.services.library_service import LibraryService


class LibraryView(Gtk.Box):
    """View for browsing and downloading stories from the online catalog."""

    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window = window
        self.library_service = LibraryService()
        self.catalog = []
        self.downloaded_stories = []
        
        self._build_ui()
        self._refresh_data()

    def _build_ui(self):
        """Build the UI components."""
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label=_("Story Library")))
        
        refresh_btn = Gtk.Button.new_from_icon_name("view-refresh")
        refresh_btn.set_tooltip_text(_("Refresh catalog"))
        refresh_btn.connect("clicked", self._on_refresh_clicked)
        header.pack_end(refresh_btn)
        
        self.append(header)

        # Status bar
        self.status_label = Gtk.Label(label=_("Loading catalog..."))
        self.status_label.set_margin_top(12)
        self.status_label.set_margin_bottom(12)
        self.status_label.add_css_class("dim-label")
        self.append(self.status_label)

        # Main content in a paned view
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)
        self.append(paned)

        # Left side: Online catalog
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        left_box.set_size_request(400, -1)
        
        catalog_label = Gtk.Label(label=_("Online Catalog"))
        catalog_label.add_css_class("title-3")
        catalog_label.set_margin_start(12)
        catalog_label.set_margin_top(12)
        left_box.append(catalog_label)

        # Language filter
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        filter_box.set_margin_start(12)
        filter_box.set_margin_end(12)
        
        filter_label = Gtk.Label(label=_("Language:"))
        filter_box.append(filter_label)
        
        self.language_filter = Gtk.DropDown()
        lang_model = Gtk.StringList()
        lang_model.append(_("All"))
        lang_model.append("Svenska")
        lang_model.append("English")
        self.language_filter.set_model(lang_model)
        self.language_filter.set_selected(0)
        self.language_filter.connect("notify::selected", self._on_language_filter_changed)
        filter_box.append(self.language_filter)

        left_box.append(filter_box)

        # Online stories list
        scrolled_online = Gtk.ScrolledWindow()
        scrolled_online.set_vexpand(True)
        scrolled_online.set_margin_start(12)
        scrolled_online.set_margin_end(12)
        
        self.online_listbox = Gtk.ListBox()
        self.online_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.online_listbox.add_css_class("boxed-list")
        scrolled_online.set_child(self.online_listbox)
        left_box.append(scrolled_online)

        paned.set_start_child(left_box)

        # Right side: Downloaded stories
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        right_box.set_size_request(400, -1)
        
        downloaded_label = Gtk.Label(label=_("Downloaded Stories"))
        downloaded_label.add_css_class("title-3")
        downloaded_label.set_margin_start(12)
        downloaded_label.set_margin_top(12)
        right_box.append(downloaded_label)

        scrolled_downloaded = Gtk.ScrolledWindow()
        scrolled_downloaded.set_vexpand(True)
        scrolled_downloaded.set_margin_start(12)
        scrolled_downloaded.set_margin_end(12)
        
        self.downloaded_listbox = Gtk.ListBox()
        self.downloaded_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.downloaded_listbox.add_css_class("boxed-list")
        scrolled_downloaded.set_child(self.downloaded_listbox)
        right_box.append(scrolled_downloaded)

        paned.set_end_child(right_box)

    def _refresh_data(self):
        """Refresh both online catalog and downloaded stories."""
        self.status_label.set_text(_("Loading catalog..."))
        threading.Thread(target=self._load_catalog_async, daemon=True).start()
        self._load_downloaded_stories()

    def _load_catalog_async(self):
        """Load catalog in background thread."""
        try:
            self.catalog = self.library_service.fetch_catalog()
            GLib.idle_add(self._update_catalog_ui)
        except Exception as e:
            GLib.idle_add(self._show_catalog_error, str(e))

    def _update_catalog_ui(self):
        """Update the catalog UI on main thread."""
        # Clear existing items
        while True:
            row = self.online_listbox.get_first_child()
            if row is None:
                break
            self.online_listbox.remove(row)

        # Add stories based on language filter
        selected_lang = self._get_selected_language()
        filtered_stories = self._filter_stories_by_language(selected_lang)
        
        for story_info in filtered_stories:
            row = self._create_catalog_row(story_info)
            self.online_listbox.append(row)
        
        count = len(filtered_stories)
        self.status_label.set_text(_("Found {count} stories in catalog").format(count=count))

    def _get_selected_language(self) -> str:
        """Get the selected language filter."""
        selected = self.language_filter.get_selected()
        if selected == 0:
            return "all"
        elif selected == 1:
            return "sv"
        else:
            return "en"

    def _filter_stories_by_language(self, lang: str) -> list:
        """Filter stories by language."""
        if lang == "all":
            return self.catalog
        return [s for s in self.catalog if s.get("language") == lang]

    def _create_catalog_row(self, story_info: dict) -> Gtk.ListBoxRow:
        """Create a row for an online story."""
        row = Gtk.ListBoxRow()
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        main_box.set_margin_top(8)
        main_box.set_margin_bottom(8)
        
        # Story info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)
        
        title_label = Gtk.Label(label=story_info.get("title", ""))
        title_label.set_halign(Gtk.Align.START)
        title_label.add_css_class("heading")
        info_box.append(title_label)
        
        desc_label = Gtk.Label(label=story_info.get("description", ""))
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_wrap(True)
        desc_label.add_css_class("body")
        desc_label.add_css_class("dim-label")
        info_box.append(desc_label)
        
        # Meta info
        meta_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        lang_label = Gtk.Label(label=f"🌐 {story_info.get('language', '').upper()}")
        lang_label.add_css_class("caption")
        meta_box.append(lang_label)
        
        age_label = Gtk.Label(label=f"👶 {story_info.get('age_group', '')}")
        age_label.add_css_class("caption")
        meta_box.append(age_label)
        
        info_box.append(meta_box)
        main_box.append(info_box)
        
        # Download button
        is_downloaded = self._is_story_downloaded(story_info.get("id"))
        if is_downloaded:
            btn = Gtk.Button(label=_("Downloaded"))
            btn.set_sensitive(False)
            btn.add_css_class("flat")
        else:
            btn = Gtk.Button(label=_("Download"))
            btn.add_css_class("suggested-action")
            btn.connect("clicked", self._on_download_clicked, story_info)
        
        btn.set_valign(Gtk.Align.CENTER)
        main_box.append(btn)
        
        row.set_child(main_box)
        return row

    def _is_story_downloaded(self, story_id: str) -> bool:
        """Check if a story is already downloaded."""
        return story_id in [s.get("id") for s in self.downloaded_stories]

    def _load_downloaded_stories(self):
        """Load list of downloaded stories."""
        self.downloaded_stories = self.library_service.get_downloaded_stories()
        self._update_downloaded_ui()

    def _update_downloaded_ui(self):
        """Update the downloaded stories UI."""
        # Clear existing items
        while True:
            row = self.downloaded_listbox.get_first_child()
            if row is None:
                break
            self.downloaded_listbox.remove(row)

        # Add downloaded stories
        for story_info in self.downloaded_stories:
            row = self._create_downloaded_row(story_info)
            self.downloaded_listbox.append(row)

    def _create_downloaded_row(self, story_info: dict) -> Gtk.ListBoxRow:
        """Create a row for a downloaded story."""
        row = Gtk.ListBoxRow()
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        main_box.set_margin_top(8)
        main_box.set_margin_bottom(8)
        
        # Story info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)
        
        title_label = Gtk.Label(label=story_info.get("title", ""))
        title_label.set_halign(Gtk.Align.START)
        title_label.add_css_class("heading")
        info_box.append(title_label)
        
        desc_label = Gtk.Label(label=story_info.get("description", ""))
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_wrap(True)
        desc_label.add_css_class("body")
        desc_label.add_css_class("dim-label")
        info_box.append(desc_label)
        
        main_box.append(info_box)
        
        # Action buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        play_btn = Gtk.Button(label=_("Play"))
        play_btn.add_css_class("suggested-action")
        play_btn.connect("clicked", self._on_play_downloaded_clicked, story_info)
        btn_box.append(play_btn)
        
        delete_btn = Gtk.Button.new_from_icon_name("user-trash")
        delete_btn.set_tooltip_text(_("Delete"))
        delete_btn.connect("clicked", self._on_delete_downloaded_clicked, story_info)
        btn_box.append(delete_btn)
        
        btn_box.set_valign(Gtk.Align.CENTER)
        main_box.append(btn_box)
        
        row.set_child(main_box)
        return row

    def _on_refresh_clicked(self, button):
        """Handle refresh button click."""
        self._refresh_data()

    def _on_language_filter_changed(self, dropdown, param):
        """Handle language filter change."""
        self._update_catalog_ui()

    def _on_download_clicked(self, button, story_info):
        """Handle download button click."""
        button.set_sensitive(False)
        button.set_label(_("Downloading..."))
        
        def download_async():
            try:
                self.library_service.download_story(story_info)
                GLib.idle_add(self._on_download_complete, button, story_info)
            except Exception as e:
                GLib.idle_add(self._on_download_error, button, str(e))
        
        threading.Thread(target=download_async, daemon=True).start()

    def _on_download_complete(self, button, story_info):
        """Handle successful download."""
        button.set_label(_("Downloaded"))
        button.add_css_class("flat")
        button.remove_css_class("suggested-action")
        self._load_downloaded_stories()

    def _on_download_error(self, button, error):
        """Handle download error."""
        button.set_sensitive(True)
        button.set_label(_("Download"))
        # TODO: Show error toast
        print(f"Download error: {error}")

    def _on_play_downloaded_clicked(self, button, story_info):
        """Handle play downloaded story."""
        if not self.window.current_profile:
            # TODO: Show profile selection dialog
            return
        
        # Load and start the story
        story = self.library_service.load_downloaded_story(story_info["id"])
        if story:
            # Reset story progress
            story.current_node_id = "start"
            story.is_complete = False
            story.profile_id = self.window.current_profile.id
            
            # Navigate to story view
            self.window.show_story_from_library(story)

    def _on_delete_downloaded_clicked(self, button, story_info):
        """Handle delete downloaded story."""
        dialog = Adw.MessageDialog(
            transient_for=self.window,
            heading=_("Delete story?"),
            body=_("This will permanently delete '{title}' from your device.").format(
                title=story_info.get("title", "")
            )
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("delete", _("Delete"))
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_delete_dialog_response, story_info)
        dialog.present()

    def _on_delete_dialog_response(self, dialog, response, story_info):
        """Handle delete confirmation dialog response."""
        if response == "delete":
            self.library_service.delete_downloaded_story(story_info["id"])
            self._load_downloaded_stories()

    def _show_catalog_error(self, error):
        """Show catalog loading error."""
        self.status_label.set_text(_("Failed to load catalog: {error}").format(error=error))