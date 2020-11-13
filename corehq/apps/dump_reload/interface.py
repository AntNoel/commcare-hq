import gzip
import os
import re
import sys
import warnings
from abc import ABCMeta, abstractmethod, abstractproperty

from corehq.util.log import with_progress_bar


class DataDumper(metaclass=ABCMeta):
    """
    :param domain: Name of domain to dump data for
    :param excludes: List of app labels ("app_label.model_name" or "app_label") to exclude
    """

    @abstractproperty
    def slug(self):
        raise NotImplementedError

    def __init__(self, domain, excludes, stdout=None, stderr=None):
        self.domain = domain
        self.excludes = excludes
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr

    @abstractmethod
    def dump(self, output_stream):
        """
        Dump data for domain to stream.
        :param output_stream: Stream to write json encoded objects to
        :return: Counter object with keys being app model labels and values being number of models dumped
        """
        raise NotImplementedError


class DataLoader(metaclass=ABCMeta):
    def __init__(self, object_filter=None, stdout=None, stderr=None):
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.object_filter = re.compile(object_filter, re.IGNORECASE) if object_filter else None

    @abstractproperty
    def slug(self):
        raise NotImplementedError

    @abstractmethod
    def load_objects(self, object_strings, force=False):
        """
        :param object_strings: iterable of JSON encoded object strings
        :param force: True if objects should be loaded into an existing domain
        :return: loaded object Counter
        """
        raise NotImplementedError

    def load_from_file(self, extracted_dump_path, dump_meta, force=False):
        file_path = os.path.join(extracted_dump_path, '{}.gz'.format(self.slug))
        if not os.path.isfile(file_path):
            raise Exception("Dump file not found: {}".format(file_path))

        self.stdout.write(f"Inspecting {file_path} using '{self.slug}' data loader.")
        expected_count = sum(dump_meta[self.slug].values())
        with gzip.open(file_path) as dump_file:
            object_strings = with_progress_bar(dump_file, length=expected_count, stream=self.stdout)
            loaded_object_count = self.load_objects(object_strings, force)

        # Warn if the file we loaded contains 0 objects.
        if sum(loaded_object_count.values()) == 0:
            warnings.warn(
                "No data found for '%s'. (File format may be "
                "invalid.)" % file_path,
                RuntimeWarning
            )

        return loaded_object_count
