# https://github.com/caxefaizan/nilmtk/blob/72da885368d3dcb40a2278a02edb5ca673f60f9d/docs/manual/user_guide/siteonlyapi_tutorial.ipynb
# https://github.com/nilmtk/nilmtk/issues/511
# https://github.com/nilmtk/nilmtk/issues/391

# physical_quantity,power,energy,voltage
# type,active,reactive,
# ,,,

from nilmtk.nilmtk.measurement import LEVEL_NAMES
from posixpath import join
from sys import stdout
from nilmtk.nilmtk.utils import check_directory_exists, get_datastore, get_module_directory
import pandas as pd
import numpy as np
from nilmtk.datastore import Key
from nilm_metadata import save_yaml_to_datastore

def convert_hb(file_path, output_filename, format='HDF'):

    print("Checando diretório")
    check_directory_exists(file_path)

    def measurement_mapping_func(house_id, chan_id):
        if chan_id <= 1:
            return [('voltage', ''), ('current', ''), ('power', 'active'), ('frequency', ""), ('power factor', "")]
        else:
            return [('power', 'active'), ('power', 'apparent'), ('power', 'reactive'), ('power factor', ""), ('voltage', ""), ('current', '')]

    # Open DataStore
    store = get_datastore(output_filename, format='HDF', mode='w')
    # print(f"{store=}")

    tz = 'America/Fortaleza' 
    sort_index=False
    drop_duplicates=False

    house_id = 1
    chans = [1, 2, 3]
    chans_filename = ["meter1", "meter2", "meter3"]

    for chan_id in chans:
            print(chan_id, end=" ")
            stdout.flush()

            key = Key(building=house_id, meter=chan_id)
            print(f"{key=}")

            measurements = measurement_mapping_func(house_id, chan_id)
            print(f"{measurements=}")

            df = pd.read_csv(chans_filename[chan_id], sep=' ', names=measurements,
                     dtype={m:np.float32 for m in measurements})
            print (df.head)

            # Modify the column labels to reflect the power measurements recorded.
            df.columns.set_names(LEVEL_NAMES, inplace=True)
            print (df.head)

            # Convert the integer index column to timezone-aware datetime 
            df.index = pd.to_datetime(df.index.values, unit='ms', utc=True)
            #df['Unix'] = pd.to_datetime(df['Unix'], unit='s', utc=True)
            df = df.tz_convert(tz)
            print (df.head)

            # raw REDD data isn't always sorted
            if sort_index:
                df = df.sort_index() 
            
            # Remove entries with duplicated timestamp (keeps the first value)
            if drop_duplicates:
                dups_in_index = df.index.duplicated(keep='first')
                if dups_in_index.any():
                    df = df[~dups_in_index]

            print (df.head)
            store.put(str(key), df)

    # Add metadata
    save_yaml_to_datastore(join(get_module_directory(), 
                            'dataset_converters', 
                            'hb', 
                            'metadata'),
                        store)
    store.close()