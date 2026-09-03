import io
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# config.py reads these at import time, so they must be set up before any
# module that (transitively) imports config/container/yamlhandler is loaded.
_TMPDIR = tempfile.mkdtemp()
os.makedirs(f'{_TMPDIR}/inventory/group_vars/ccc-cluster', exist_ok=True)
with open(f'{_TMPDIR}/inventory/hosts.yml', 'w') as _f:
    _f.write('all: {}\n')
open(f'{_TMPDIR}/inventory/group_vars/ccc-cluster/user-list.yml', 'w').close()
open(f'{_TMPDIR}/inventory/group_vars/ccc-cluster/user-containers.yml', 'w').close()

os.environ.setdefault('PORT_PASSWORD_FORMAT', '{}')
os.environ['CCC_INVENTORY_DIR'] = _TMPDIR

with patch('container.get_available_images', return_value=['vicoslab/ccc:image1']):
    import yamlhandler

RESEARCHER_HEADER = '  ' + '#' * 30 + ' ## ViCoS Researchers ' + '#' * 9 + ' ' + '#' * 30 + '\n'
STUDENT_PHD_HEADER = '  ' + '#' * 30 + ' ## ViCoS Students ' + '#' * 12 + ' ' + '#' * 30 + ' # PhD students\n'
STUDENT_HEADER = '  # Other\n'
LKM_HEADER = '  ' + '#' * 30 + ' ## LKM Researchers/students ## ' + '#' * 30 + '\n'


def _user_entry(email, name, role):
    return f'  {email}:\n    USER_FULLNAME: {name}\n    USER_EMAIL: {email}\n    USER_TYPE: {role}\n'


def _container_entry(stack, storage, email):
    return (
        f'  - STACK_NAME: {stack}\n'
        f'    STORAGE_NAME: {storage}\n'
        f'    USER_EMAIL: {email}\n'
        f"    CONTAINER_IMAGE: vicoslab/ccc:image1\n"
        f"    INSTALL_PACKAGES: ''\n"
    )


def build_state():
    """Build a minimal, self-consistent session state with one user/container
    per group, loaded and then round-tripped through save_users/save_containers
    so that the resulting plaintext exactly matches what has_pending_changes
    compares against when there are no edits."""

    user_full = (
        'deployment_types:\n  researcher: {}\n  student: {}\n  student_LKM: {}\n'
        + RESEARCHER_HEADER + _user_entry('user1@example.com', 'User One', 'researcher')
        + STUDENT_PHD_HEADER + _user_entry('user2@example.com', 'User Two', 'researcher')
        + STUDENT_HEADER + _user_entry('user3@example.com', 'User Three', 'student')
        + LKM_HEADER + _user_entry('user4@example.com', 'User Four', 'student_LKM')
    )

    container_full = (
        'deployment_containers: []\n'
        + RESEARCHER_HEADER + _container_entry('stack1', 'storage1', 'user1@example.com')
        + STUDENT_PHD_HEADER + _container_entry('stack2', 'storage2', 'user2@example.com')
        + STUDENT_HEADER + _container_entry('stack3', 'storage3', 'user3@example.com')
        + LKM_HEADER + _container_entry('stack4', 'storage4', 'user4@example.com')
    )

    state = {'_user_plaintext': user_full, '_container_plaintext': container_full}
    with patch('container.get_available_images', return_value=['vicoslab/ccc:image1']):
        yamlhandler.load_users(state)
        yamlhandler.load_containers(state)

        # Canonicalize the plaintext by round-tripping it once, so a freshly
        # loaded (unmodified) state is never reported as having pending changes.
        user_buf = io.StringIO()
        yamlhandler.save_users(state, user_buf)
        container_buf = io.StringIO()
        yamlhandler.save_containers(state, container_buf)

        state['_user_plaintext'] = user_buf.getvalue()
        state['_container_plaintext'] = container_buf.getvalue()
        yamlhandler.load_users(state)
        yamlhandler.load_containers(state)

    return state


class HasPendingChangesTests(unittest.TestCase):
    def test_no_changes_reports_false(self):
        state = build_state()
        self.assertFalse(yamlhandler.has_pending_changes(state))

    def test_user_edit_is_detected(self):
        state = build_state()
        state['user_df']['Researcher'].loc['user1@example.com', 'USER_FULLNAME'] = 'Changed Name'
        self.assertTrue(yamlhandler.has_pending_changes(state))

    def test_container_edit_is_detected(self):
        state = build_state()
        state['container_df']['Researcher'].loc[0, 'STACK_NAME'] = 'stack1-renamed'
        self.assertTrue(yamlhandler.has_pending_changes(state))

    def test_missing_plaintext_reports_false(self):
        self.assertFalse(yamlhandler.has_pending_changes({}))


if __name__ == '__main__':
    unittest.main()
