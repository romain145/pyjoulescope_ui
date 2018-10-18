# Copyright 2018 Jetperch LLC
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This executable captures the raw USB stream from Joulescope devices
and saves the raw stream data to a file.  This executable is a
development tool and is not intended for customer use.
"""

import logging
from joulescope_ui.main import run


NAME = "ui"


def parser_config(p):
    """Start the Joulescope graphical user interface"""
    return on_cmd


def on_cmd(args):
    return run()