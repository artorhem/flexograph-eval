"""
Shared utility module for reading and parsing dataset properties files.

This module provides a PropertiesReader class that can be used across different
graph processing system benchmarking scripts to read dataset properties files
and extract relevant information like supported algorithms, source vertices, etc.
"""

import os
import configparser


class PropertiesReader:
    """
    A class to read and parse dataset properties files.

    The properties files contain information about datasets including:
    - Supported algorithms
    - Source vertices for BFS, SSSP, etc.
    - Graph metadata (vertices, edges, directed/undirected)
    - Algorithm-specific parameters
    """

    # Common algorithm mappings for different systems
    ALGORITHM_MAPPINGS = {
        'gapbs': {
            'bfs': 'bfs',
            'pr': 'pr',
            'wcc': 'cc',  # WCC (weakly connected components) maps to cc
            'sssp': 'sssp',
            'lcc': None,  # LCC (local clustering coefficient) not supported
            'cdlp': None,  # CDLP (community detection label propagation) not supported
        },
        'ligra': {
            'bfs': 'BFS',
            'pr': 'PageRank',
            'wcc': 'Components',
            'sssp': None,  # SSSP not commonly available in Ligra
            'lcc': 'Triangle',  # Triangle counting, closest to LCC
            'cdlp': None,
        },
        'gemini': {
            'bfs': 'bfs',
            'pr': 'pagerank',
            'wcc': 'cc',
            'sssp': 'sssp',
            'lcc': None,
            'cdlp': None,
        },
        'galois': {
            'bfs': 'bfs',
            'pr': 'pagerank',
            'wcc': 'cc',
            'sssp': 'sssp',
            'lcc': None,
            'cdlp': None,
        },
    }

    def __init__(self, dataset_name, dataset_path, system_name=None):
        """
        Initialize the PropertiesReader.

        Args:
            dataset_name: Name of the dataset (e.g., 'graph500_23')
            dataset_path: Path to the dataset directory
            system_name: Optional name of the system (e.g., 'gapbs', 'ligra')
                        Used for algorithm mapping
        """
        self.dataset_name = dataset_name
        self.dataset_path = dataset_path
        self.system_name = system_name
        self.properties_file = f"{dataset_path}/{dataset_name}.properties"
        self._properties = None

    def read(self):
        """
        Read and parse the properties file.

        Returns:
            dict: Dictionary containing parsed properties, or None if file not found
                 Dictionary keys:
                 - 'algorithms': list of algorithm names
                 - 'bfs_source': BFS source vertex (string or None)
                 - 'sssp_source': SSSP source vertex (string or None)
                 - 'directed': boolean indicating if graph is directed
                 - 'vertices': number of vertices (int or None)
                 - 'edges': number of edges (int or None)
                 - 'raw_config': raw ConfigParser object for custom queries
        """
        if not os.path.exists(self.properties_file):
            print(f"Properties file not found: {self.properties_file}")
            return None

        config = configparser.ConfigParser()
        # Properties files don't have section headers, so we add a DEFAULT section
        with open(self.properties_file, 'r') as f:
            config_string = '[DEFAULT]\n' + f.read()

        config.read_string(config_string)

        # Initialize properties dictionary
        properties = {
            'algorithms': [],
            'bfs_source': None,
            'sssp_source': None,
            'directed': False,
            'vertices': None,
            'edges': None,
            'raw_config': config,
        }

        # Extract dataset key from properties (handle both formats: graph500-23 or graph500_23)
        dataset_key = self._find_dataset_key(config)

        if not dataset_key:
            print(f"Could not find dataset key in properties file for {self.dataset_name}")
            return None

        # Get algorithms list
        algo_key = f"graph.{dataset_key}.algorithms"
        if algo_key in config['DEFAULT']:
            algos_str = config['DEFAULT'][algo_key]
            properties['algorithms'] = [algo.strip() for algo in algos_str.split(',')]

        # Get BFS source vertex
        bfs_key = f"graph.{dataset_key}.bfs.source-vertex"
        if bfs_key in config['DEFAULT']:
            properties['bfs_source'] = config['DEFAULT'][bfs_key].strip()

        # Get SSSP source vertex
        sssp_key = f"graph.{dataset_key}.sssp.source-vertex"
        if sssp_key in config['DEFAULT']:
            properties['sssp_source'] = config['DEFAULT'][sssp_key].strip()

        # Get directed property
        directed_key = f"graph.{dataset_key}.directed"
        if directed_key in config['DEFAULT']:
            properties['directed'] = config['DEFAULT'][directed_key].strip().lower() == 'true'

        # Get metadata (vertices and edges)
        vertices_key = f"graph.{dataset_key}.meta.vertices"
        if vertices_key in config['DEFAULT']:
            properties['vertices'] = int(config['DEFAULT'][vertices_key].strip())

        edges_key = f"graph.{dataset_key}.meta.edges"
        if edges_key in config['DEFAULT']:
            properties['edges'] = int(config['DEFAULT'][edges_key].strip())

        self._properties = properties
        return properties

    def _find_dataset_key(self, config):
        """
        Find the dataset key in the config by searching for matching keys.
        Handles both underscore and hyphen formats (e.g., graph500_23 vs graph500-23).

        Args:
            config: ConfigParser object

        Returns:
            str: Dataset key found in properties, or None
        """
        dataset_key = None
        for key in config['DEFAULT']:
            if self.dataset_name.replace('_', '-') in key or self.dataset_name in key:
                dataset_key = key.split('.')[1]
                break
        return dataset_key

    def get_mapped_algorithms(self, custom_mapping=None):
        """
        Get algorithms mapped to system-specific names.

        Args:
            custom_mapping: Optional dictionary mapping property algorithm names
                          to system-specific names. If not provided, uses the
                          system_name to look up a predefined mapping.

        Returns:
            list: List of system-specific algorithm names that are supported
        """
        if self._properties is None:
            self.read()

        if self._properties is None:
            return []

        # Determine which mapping to use
        mapping = custom_mapping
        if mapping is None and self.system_name:
            mapping = self.ALGORITHM_MAPPINGS.get(self.system_name, {})

        if not mapping:
            # No mapping available, return algorithms as-is
            return self._properties['algorithms']

        # Map algorithms
        mapped_algorithms = []
        for algo in self._properties['algorithms']:
            if algo in mapping and mapping[algo] is not None:
                system_algo = mapping[algo]
                if system_algo not in mapped_algorithms:
                    mapped_algorithms.append(system_algo)

        return mapped_algorithms

    def get_source_vertex(self, algorithm):
        """
        Get the source vertex for a specific algorithm.

        Args:
            algorithm: Algorithm name (e.g., 'bfs', 'sssp')

        Returns:
            str: Source vertex as string, or None if not found
        """
        if self._properties is None:
            self.read()

        if self._properties is None:
            return None

        if algorithm.lower() == 'bfs':
            return self._properties['bfs_source']
        elif algorithm.lower() == 'sssp':
            return self._properties['sssp_source']

        return None

    def is_directed(self):
        """
        Check if the graph is directed.

        Returns:
            bool: True if directed, False if undirected
        """
        if self._properties is None:
            self.read()

        if self._properties is None:
            return False

        return self._properties['directed']

    def get_property(self, key):
        """
        Get a specific property by key.

        Args:
            key: Property key name

        Returns:
            Value associated with the key, or None if not found
        """
        if self._properties is None:
            self.read()

        if self._properties is None:
            return None

        return self._properties.get(key)

    def get_all_properties(self):
        """
        Get all parsed properties.

        Returns:
            dict: All properties, or None if not read yet
        """
        if self._properties is None:
            self.read()

        return self._properties

    @staticmethod
    def add_algorithm_mapping(system_name, mapping):
        """
        Add or update an algorithm mapping for a system.

        Args:
            system_name: Name of the system (e.g., 'mysystem')
            mapping: Dictionary mapping property algorithm names to system names
        """
        PropertiesReader.ALGORITHM_MAPPINGS[system_name] = mapping

    @staticmethod
    def get_available_systems():
        """
        Get list of systems with predefined algorithm mappings.

        Returns:
            list: List of system names
        """
        return list(PropertiesReader.ALGORITHM_MAPPINGS.keys())
