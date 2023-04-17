#!../venv/bin/python3
"""translate_to_indic_lang - translates to indic languages"""

import os, json, sys
from concurrent.futures import ThreadPoolExecutor

from helpers import Helpers
from inference.engine import Model


class TranslateToIndicLang:
    def __init__(self) -> None:
        """Init Function for class"""
        self.model = None
        self.helperFuncs = Helpers()
        self.cfg = self.helperFuncs.read_configfile(".config.ini")
        self.CLEAN_START = self.cfg["APP"].getboolean("CLEAN_START")
        self.TARGET_URL = self.cfg["APP"].get("TARGET_URL")
        self.SRC_LANG = self.cfg["APP"].get("SRC_LANG")
        self.TARGET_LANG = self.cfg["APP"].get("TARGET_LANG")
        self.MAX_PARALLEL_REQUESTS = self.cfg["APP"].get("MAX_PARALLEL_REQUESTS")
        self.WORK_DIR = os.getcwd() + "/" + ".work_dir"
        self.OUTPUT_FOLDERNAME = "output"
        self.INPUT_FILENAME = "input.json"
        self.INPUT_FILELOC = self.WORK_DIR + "/" + self.INPUT_FILENAME
        self.OUTPUT_FOLDERLOC = self.WORK_DIR + "/" + self.OUTPUT_FOLDERNAME

    def __initiate_model(self) -> None:
        """Instantiate Model"""
        self.model = Model(expdir="../en-indic")

    def __cleanup(self) -> None:
        """Cleanup work environment"""
        print("Initiating Cleanup ...")
        self.helperFuncs.execute_shell_command("rm -rf " + self.WORK_DIR)

    def __create_work_env(self) -> None:
        """Building work environment"""
        print("Creating work environment ...")
        self.helperFuncs.execute_shell_command("mkdir -p " + self.WORK_DIR)
        self.helperFuncs.execute_shell_command("mkdir -p " + self.OUTPUT_FOLDERLOC)

    def __download_target(self) -> None:
        """Downloading target"""
        print("Downloading target ...")
        self.helperFuncs.execute_shell_command(
            "curl "
            + self.TARGET_URL
            + " --output "
            + self.WORK_DIR
            + "/"
            + self.INPUT_FILENAME
        )

    def __read_input_file(self) -> None:
        """Collecting meta information about data"""
        data = []
        with open(self.INPUT_FILELOC, "r") as f:
            data = json.load(f)
        return data

    def __initialize_setup(self) -> None:
        """initializing setup"""
        if (not os.path.exists(self.WORK_DIR)) and (not self.CLEAN_START):
            self.__cleanup()
            self.__create_work_env()
            self.__download_target()
            os.environ["PYTHONPATH"] = os.getcwd() + "/fairseq/"

    def translate_text(self, value):
        """translate text from source to target language"""
        if "\n" in value:
            replace_dn = value.replace("\n\n", "\n")
            split_lines = replace_dn.splitlines()
            text_splits = self.model.batch_translate(
                split_lines, self.SRC_LANG, self.TARGET_LANG
            )
            response = "\n".join(text_splits)
        else:
            response = self.model.translate_paragraph(
                value, self.SRC_LANG, self.TARGET_LANG
            )
        return response.strip()

    def translate_item(self, item) -> None:
        """translate item"""
        translated_item = {}
        for key, value in item.items():
            if value:
                translated_value = self.translate_text(value)
                translated_item[key] = translated_value
                translated_item["english_" + key] = value
            else:
                translated_item[key] = ""
                translated_item["english_" + key] = ""
        return translated_item

    def save_item(self, item, filename):
        """Save translated file"""
        with open(filename, "w") as f:
            json.dump(item, f, ensure_ascii=False, indent=4)

    def translate_and_save(self, item, i):
        """translating and saving to file"""
        output_fname = self.OUTPUT_FOLDERLOC + "/" + f"translated_{i}.json"
        if os.path.isfile(output_fname):
            return
        else:
            translated_item = self.translate_item(item)
            self.save_item(translated_item, output_fname)
            print("Successfully translated - " + output_fname)

    def run_translation(self) -> None:
        data = self.__read_input_file()
        print("Working with - " + str(len(data)) + " elements ...")

        # with ThreadPoolExecutor(max_workers=self.MAX_PARALLEL_REQUESTS) as executor:
        #     futures = {
        #         executor.submit(self.translate_and_save, item, i)
        #         for i, item in enumerate(data)
        #     }

        for i, item in enumerate(data):
            self.translate_and_save(item, i)
            sys.exit()

    def run(self):
        self.__initialize_setup()
        self.__initiate_model()
        self.run_translation()


TranslateToIndicLang().run()
