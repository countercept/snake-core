"""The file storage module."""

import hashlib
import os
from os import path
import shutil
import string

import magic

from snake import error
from snake.config import snake_config


class FileStorage():
    """File storage, used to manage files through snake.

    Attributes:
        sha256_digest (str): The hash of the file.
        file_path (str): The path to the file.
        magic (str): The magic of the file.
        mime (str): The mime of the file.
        size (int): The size of the file.
    """

    def __init__(self, sha256_digest=None):
        self.sha256_digest = sha256_digest
        if self.sha256_digest:
            try:
                self.file_path = self.path()
                self.magic = magic.from_file(self.file_path)
                self.mime = magic.from_file(self.file_path, mime=True)
                self.size = self._size()
            except FileNotFoundError:
                raise error.ServerError('File not found on disk')
            return

    def to_dict(self):
        """Dictionary representation of the class.

        Returns:
            dict: A dictionary containing: magic, mime, sha256_digest and size.
        """
        return {
            'magic': self.magic,
            'mime': self.mime,
            'sha256_digest': self.sha256_digest,
            'size': self.size
        }

    def save(self, move=False):
        """Save storage file.

        This will only save the file if the paths don't match. It will only
        save by copying so the original file remains intact.

        Args:
            move (bool, optional): Whether to move or just copy the file.
                Defaults to False.

        Returns:
            bool: True on success, False on failure.
        """
        # Only save if the path does NOT match
        true_path = self.path()
        if self.file_path == true_path:
            return True
        directory, _ = path.split(true_path)
        os.makedirs(directory, exist_ok=True)
        if move:
            if not shutil.move(self.file_path, true_path):
                return False
        else:
            if not shutil.copy(self.file_path, true_path):
                return False
        self.file_path = true_path
        return True

    def create(self, file_path, sha256_digest=None):
        """Create storage file.

        This function is used to create a file and should only be called on a
        clean FileStorage instance. It will not save the object to disk, the
        save function must be called to do this. If the sha256_digest is not
        provided it will be calculated.

        Args:
            file_path (str): The path to the file.
            sha256_digest (str, optional): The hash for the file.
                Defaults to None.

        Returns:
            bool: True on success, False on failure.
        """
        self.file_path = file_path
        self.sha256_digest = sha256_digest
        if not self.sha256_digest:
            sha2 = hashlib.sha256()
            with open(self.file_path, 'rb') as f:
                chunk = f.read(4096)
                while chunk:
                    sha2.update(chunk)
                    chunk = f.read(4096)
            self.sha256_digest = sha2.hexdigest()
        self.magic = magic.from_file(self.file_path)
        self.mime = magic.from_file(self.file_path, mime=True)
        self.size = self._size()
        return True

    def delete(self):
        """Delete storage file.

        Returns:
            bool: True on success, False on failure.
        """
        if self.file_path == self.path():
            return os.remove(self.file_path)
        return False

    def directory(self):
        """Get the directory for the storage file.

        Returns:
            str: Directory to the storage file.
        """
        return path.join(path.abspath(path.expanduser(snake_config['file_db'])), self.sha256_digest[0:2], self.sha256_digest[2:4])

    def path(self):
        """Get the path for the storage file.

        Returns:
            str: Path to the storage file.
        """
        return path.join(path.abspath(path.expanduser(snake_config['file_db'])), self.sha256_digest[0:2], self.sha256_digest[2:4], self.sha256_digest)

    def _size(self):
        self.size = path.getsize(self.file_path)
        return self.size

    def to_hexdump(self, lines=16):
        """Create a hex dump for the storage file.

        Args:
            lines (int): Number of lines to hexdump. Defaults to 16.

        Returns:
            str: hexdump of storage file.
        """
        buf = ''
        with open(self.file_path, 'rb') as f:
            counter = 0
            for chunk in iter(lambda: f.read(16), b""):
                if counter >= lines:
                    break
                _hex = [('%02x' % i) for i in chunk]
                buf += '%07x: %-39s  %s\n' % (
                    (counter * 16),
                    (' '.join([''.join(_hex[i:i + 2]) for i in range(0, len(_hex), 2)])),
                    (''.join([chr(c) if chr(c) in string.printable[:-5] else '.' for c in chunk])))
                counter += 1
        return buf
