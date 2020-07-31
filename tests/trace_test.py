import platform
import unittest
import subprocess
from pathlib import Path
from timeit import default_timer as timer
import gtirb

ex_dir = Path("./examples/trace_examples/")
funinfer = Path("./build/bin/funinfer")
tbgtirb = "tbdisasm_a_20200713.gtirb"


# This is duplicated from disassemble_reassemble_check.py
# TODO: Move to some more general shared utility module, maybe?
class bcolors:
    """
    Define some colors for printing in the terminal
    """

    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"

    @classmethod
    def okblue(cls, *args):
        return cls.OKBLUE + " ".join(args) + cls.ENDC

    @classmethod
    def okgreen(cls, *args):
        return cls.OKGREEN + " ".join(args) + cls.ENDC

    @classmethod
    def warning(cls, *args):
        return cls.WARNING + " ".join(args) + cls.ENDC

    @classmethod
    def fail(cls, *args):
        return cls.FAIL + " ".join(args) + cls.ENDC


class TraceFunctionInference(unittest.TestCase):
    def get_function_addresses(self, module):
        addresses = set()
        for _, entrySet in module.aux_data.get("functionEntries").data.items():
            for block in entrySet:
                addresses.add(block.address)
        return addresses

    @unittest.skipUnless(
        platform.system() == "Linux", "This test is linux only."
    )
    @unittest.skipUnless(
        funinfer.exists(), "This test requires funinfer to be built."
    )
    def test_function_inference(self):
        """
        Test that the trace function inference finds at least the known number
        of functions in the test case binary.
        """
        gtirb_out = "ff_" + tbgtirb
        print(bcolors.okblue("# Function Inference " + tbgtirb + "\n"))
        start = timer()
        completedProcess = subprocess.run(
            [
                funinfer.as_posix(),
                (ex_dir / tbgtirb).as_posix(),
                "--ir",
                gtirb_out,
                "-j",
                "1",
            ]
        )
        time_spent = timer() - start
        if completedProcess.returncode == 0:
            print(bcolors.okgreen("Function inference succeeded"), flush=True)
        else:
            print(
                bcolors.fail(
                    "Function inference failed "
                    + str(completedProcess.returncode)
                ),
                flush=True,
            )
            return False, time_spent
        ir_ff = gtirb.IR.load_protobuf(gtirb_out)
        modules = ir_ff.modules
        nfb = 0
        nfe = 0
        for module in modules:
            if "functionBlocks" in module.aux_data:
                nfb += len(module.aux_data["functionBlocks"].data)
            if "functionEntries" in module.aux_data:
                nfe += len(module.aux_data["functionEntries"].data)
        self.assertTrue(
            nfb >= 229
            and "Failed to discover expected number of function blocks."
        )
        self.assertTrue(
            nfe >= 229
            and "Failed to discover expected number of function entries."
        )


if __name__ == "__main__":
    unittest.main()
