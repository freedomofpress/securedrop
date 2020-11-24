from . import source_navigation_steps, journalist_navigation_steps
from . import functional_test
from sdconfig import config


class TestSourceInterfaceDesignationCollision(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin):

    def start_source_server(self, source_port):
        self.source_app.crypto_util.adjectives = \
            self.source_app.crypto_util.adjectives[:1]
        self.source_app.crypto_util.nouns = self.source_app.crypto_util.nouns[:1]
        config.SESSION_EXPIRATION_MINUTES = self.session_expiration / 60.0

        self.source_app.run(port=source_port, debug=True, use_reloader=False, threaded=True)

    def test_display_id_designation_collisions(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_logs_out()
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page_with_colliding_journalist_designation()


class TestSourceInterface(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin):

    def test_lookup_codename_hint(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_shows_codename()
        self._source_hides_codename()
        self._source_logs_out()
        self._source_visits_source_homepage()
        self._source_chooses_to_login()
        self._source_proceeds_to_login()
        self._source_sees_no_codename()


class TestDownloadKey(
        functional_test.FunctionalTest,
        journalist_navigation_steps.JournalistNavigationStepsMixin):

    def test_journalist_key_from_source_interface(self):
        data = self.return_downloaded_content(self.source_location +
                                              "/public-key", None)

        data = data.decode('utf-8')
        assert "BEGIN PGP PUBLIC KEY BLOCK" in data


class TestDuplicateSourceInterface(
        functional_test.FunctionalTest,
        source_navigation_steps.SourceNavigationStepsMixin):

    def get_codename_generate(self):
        return self.driver.find_element_by_css_selector("#codename").text

    def get_codename_lookup(self):
        return self.driver.find_element_by_css_selector("#codename-hint-content p").text

    def test_duplicate_generate_pages(self):
        # Test generation of multiple codenames in different browser tabs, ref. issue 4458.

        # Generate a codename in Tab A
        assert len(self.driver.window_handles) == 1
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        codename_a = self.get_codename_generate()

        # Generate a different codename in Tab B
        self.driver.execute_script("window.open('about:blank', '_blank')")
        tab_b = self.driver.window_handles[1]
        assert len(self.driver.window_handles) == 2
        self.driver.switch_to.window(tab_b)
        assert self.driver.current_window_handle == tab_b
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        codename_b = self.get_codename_generate()

        tab_a = self.driver.window_handles[0]
        assert tab_a != tab_b
        assert codename_a != codename_b

        # Proceed to submit documents in Tab A
        assert len(self.driver.window_handles) == 2
        self.driver.switch_to.window(tab_a)
        assert self.driver.current_window_handle == tab_a
        self._source_continues_to_submit_page()
        assert self._is_on_lookup_page()
        self._source_shows_codename(verify_source_name=False)
        codename_lookup_a = self.get_codename_lookup()
        assert codename_lookup_a == codename_a
        self._source_submits_a_message()

        # Proceed to submit documents in Tab B
        self.driver.switch_to.window(tab_b)
        assert self.driver.current_window_handle == tab_b
        self._source_continues_to_submit_page()
        assert self._is_on_lookup_page()
        self._source_sees_already_logged_in_in_other_tab_message()
        self._source_shows_codename(verify_source_name=False)
        codename_lookup_b = self.get_codename_lookup()
        # We expect the codename to be the one from Tab A
        assert codename_lookup_b == codename_a
        self._source_submits_a_message()

    def test_refreshed_duplicate_generate_pages(self):
        # Test generation of multiple codenames in different browser tabs, including behavior
        # of refreshing the codemae in each tab. Ref. issue 4458.

        # Generate a codename in Tab A
        assert len(self.driver.window_handles) == 1
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        codename_a1 = self.get_codename_generate()
        # Regenerate codename in Tab A
        self._source_regenerates_codename()
        codename_a2 = self.get_codename_generate()
        assert codename_a1 != codename_a2

        # Generate a different codename in Tab B
        self.driver.execute_script("window.open('about:blank', '_blank')")
        tab_a = self.driver.window_handles[0]
        tab_b = self.driver.window_handles[1]
        self.driver.switch_to.window(tab_b)
        assert self.driver.current_window_handle == tab_b
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        codename_b = self.get_codename_generate()
        assert codename_b != codename_a1 != codename_a2

        # Proceed to submit documents in Tab A
        self.driver.switch_to.window(tab_a)
        assert self.driver.current_window_handle == tab_a
        self._source_continues_to_submit_page()
        assert self._is_on_lookup_page()
        self._source_shows_codename(verify_source_name=False)
        codename_lookup_a = self.get_codename_lookup()
        assert codename_lookup_a == codename_a2
        self._source_submits_a_message()

        # Regenerate codename in Tab B
        self.driver.switch_to.window(tab_b)
        assert self.driver.current_window_handle == tab_b
        self._source_regenerates_codename()
        # We expect the source to be directed to /lookup with a flash message
        assert self._is_on_lookup_page()
        self._source_sees_redirect_already_logged_in_message()
        # Check codename
        self._source_shows_codename(verify_source_name=False)
        codename_lookup_b = self.get_codename_lookup()
        assert codename_lookup_b == codename_a2
        self._source_submits_a_message()
