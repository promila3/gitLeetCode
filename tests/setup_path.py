import os
import sys
 
current_dir     = os.path.dirname(__file__)
relative_path   = os.path.join(current_dir, "../source")
sys.path.append(relative_path)
 