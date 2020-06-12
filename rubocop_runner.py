import os
import subprocess
import shlex
import locale

RVM_DEFAULT_PATH = '~/.rvm/bin/rvm-auto-ruby'
RBENV_DEFAULT_PATH = '~/.rbenv/bin/rbenv'

class RubocopRunner(object):
  """This class takes care of the rubocop location and its execution"""
  def __init__(self, args):
    self.set_default_paths()
    self.on_windows = False
    self.is_st2 = False
    self.custom_rubocop_cmd = ''
    self.rubocop_config_file = ''
    self.chdir = None
    vars(self).update(args)

  def set_default_paths(self):
    self.rvm_auto_ruby_path = RVM_DEFAULT_PATH
    self.rbenv_path = RBENV_DEFAULT_PATH

  def load_cmd_prefix(self):
    self.cmd_prefix = []
    if not self.load_rvm():
      self.load_rbenv()

  def load_rvm(self):
    if self.use_rvm:
      rvm_cmd = os.path.expanduser(self.rvm_auto_ruby_path)
      self.cmd_prefix = [rvm_cmd, '-S']
      return True
    return False

  def load_rbenv(self):
    if self.use_rbenv:
      rbenv_cmd = os.path.expanduser(self.rbenv_path)
      self.cmd_prefix = [rbenv_cmd, 'exec']
      return True
    return False

  def run(self, pathlist, options=[]):
    call_list = self.command_list(pathlist, options)
    use_shell = False
    if self.on_windows:
      use_shell = True

    p = subprocess.Popen(call_list, shell=use_shell,
      stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.chdir)
    out, err = p.communicate()
    return out

  def command_string(self, pathlist, options=[]):
    list = self.command_list(pathlist, options)
    return ' '.join(list)

  def command_list(self, pathlist, options=[]):
    result = []

    # Command
    if not self.custom_rubocop_cmd:
      self.load_cmd_prefix()
      result += self.cmd_prefix
      result.append('rubocop')
    else:
      if self.on_windows and self.is_st2:
        result += self.custom_rubocop_cmd.split()
      else:
        result += shlex.split(self.custom_rubocop_cmd)


    # Options
    if options:
      for option in options:
        result.append(option)
    if self.rubocop_config_file:
      result.append('-c')
      result.append(self.rubocop_config_file)

    # Paths
    for path in pathlist:
      if self.on_windows:
        path = path.replace('\\', '/')
      result.append(path)

    # ST 2 uses Python 2.6.5 which uses CreateProcessA
    # within subprocess on Windows. Does not work well
    # with strings including 0 bytes. This is a hack
    # which just removes 0 bytes from each command part.
    # This won't work with paths which include unicode
    # characters.
    if self.on_windows and self.is_st2:
      result = map(lambda s:s.replace('\x00', ''), result)

    return result
