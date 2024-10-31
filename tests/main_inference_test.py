import platform
import unittest
from disassemble_reassemble_check import compile, disassemble, cd
import yaml

from pathlib import Path

ex_dir = Path("./examples/")


class TestMainInference(unittest.TestCase):
    def setUp(self):
        self.configs = Path("./tests/").glob("*-elf-*.yaml")

    def get_main_address(self, module):
        for sym in module.symbols:
            if sym.name == "main":
                return sym.referent.address

        self.fail("No main symbol disassembled")

    def check_main_inference(
        self, make_dir, binary, strip=False, strip_exe="strip", **compile_opts
    ):
        """
        Test that the main function is inferred in the same location for
        both stripped and non-stripped versions of the same binary.
        """
        with cd(make_dir):
            self.assertTrue(compile(**compile_opts), msg="Compilation failed")
            ir = disassemble(
                binary,
                strip_exe=strip_exe,
                strip=strip,
                extra_args=["--skip-function-analysis"],
            ).ir()
            module = ir.modules[0]
            ir_stripped = disassemble(
                binary,
                Path("ex_stripped.gtirb"),
                strip_exe=strip_exe,
                strip=True,
            ).ir()
            module_stripped = ir_stripped.modules[0]
            self.assertEqual(
                self.get_main_address(module),
                self.get_main_address(module_stripped),
            )

    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    def test_main_ex1(self):
        for path in self.configs:
            # Parse YAML config file.
            with open(path) as f:
                config = yaml.safe_load(f)

            # Locate config for ex1
            for test in config["tests"]:
                if test["name"] == "ex1":
                    break
            else:
                continue  # no ex1 in this .yaml.

            arch = test.get("arch")
            strip = test["test"].get("strip", False)
            strip_exe = test["test"]["strip_exe"]
            exec_wrapper = test["test"]["wrapper"]
            compilers = test["build"]["c"]
            # just use the first cxx compiler (shouldn't be used for ex1)
            cxx_compiler = test["build"]["cpp"][0]
            extra_flags = test["build"]["flags"]

            for optimizations in test["build"]["optimizations"]:
                for compiler in compilers:
                    with self.subTest(
                        compiler=compiler, optimizations=optimizations
                    ):
                        self.check_main_inference(
                            ex_dir / "ex1",
                            Path("ex"),
                            strip=strip,
                            strip_exe=strip_exe,
                            compiler=compiler,
                            cxx_compiler=cxx_compiler,
                            optimizations=optimizations,
                            extra_flags=extra_flags,
                            arch=arch,
                            exec_wrapper=exec_wrapper,
                        )


if __name__ == "__main__":
    unittest.main()
