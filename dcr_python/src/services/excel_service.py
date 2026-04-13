"""
Excel export service for raw traffic data
"""
import os
import pandas as pd
from typing import Dict, Any, List, Optional
from ..core.analytics import AnalyticsEngine

class ExcelService:
    """Service for generating raw Excel data extracts"""

    @staticmethod
    def export_raw_data(df: pd.DataFrame, metadata: Dict[str, Any], folder_path: str) -> str:
        """
        Export raw traffic data to an Excel file.
        
        Args:
            df: The traffic DataFrame
            metadata: Metadata dictionary
            folder_path: Target folder
            
        Returns:
            The path to the generated file
        """
        file_path = os.path.join(folder_path, "Données_brut.xlsx")
        
        # Prepare Metadata table
        # We need a list of (key, value) pairs for the metadata sheet
        # Usually from self.metadata_fields in the legacy UI
        meta_items = [
            ("Date de début", metadata.get('start_datetime', '--')),
            ("Date de fin", metadata.get('end_datetime', '--')),
            ("TMJ VL Sens 1", metadata.get('tmj_vl_sens1', '--')),
            ("TMJ VL Sens 2", metadata.get('tmj_vl_sens2', '--')),
            ("TMJ PL Sens 1", metadata.get('tmj_pl_sens1', '--')),
            ("TMJ PL Sens 2", metadata.get('tmj_pl_sens2', '--')),
        ]
        df_meta = pd.DataFrame(meta_items, columns=["Champ", "Valeur"])

        # Prepare Comptages
        df_export = df.copy()
        df_export['Date'] = df_export['timestamp'].dt.strftime('%d/%m/%Y')
        df_export['Heure'] = df_export['timestamp'].dt.strftime('%H:%M')

        def build_comptages(direction_label):
            sub = df_export[df_export['direction'] == direction_label]
            vl = sub[sub['vehicle_class'] == 'VL'].groupby(['Date', 'Heure'])['count'].sum()
            pl = sub[sub['vehicle_class'] == 'PL'].groupby(['Date', 'Heure'])['count'].sum()
            keys = sorted(set(vl.index) | set(pl.index))
            rows = [[d, h, int(vl.get((d, h), 0)), int(pl.get((d, h), 0)), int(vl.get((d, h), 0) + pl.get((d, h), 0))] for d, h in keys]
            return pd.DataFrame(rows, columns=['Date', 'Heure', 'VL', 'PL', 'TV'])

        df_s1 = build_comptages('Sens 1')
        df_s2 = build_comptages('Sens 2')

        # Speed data
        bin_cols = [f"Bin{i+1}" for i in range(12)]
        speed_centers = metadata.get('speed_bin_centers', [15, 35, 45, 55, 65, 75, 85, 95, 105, 115, 125, 140])

        def build_vitesse(direction, vehicle_class):
            sub = df_export[(df_export['direction'] == direction) & (df_export['vehicle_class'] == vehicle_class)].copy()
            grouped = sub.groupby(['Date', 'Heure'])[bin_cols].sum().reset_index()
            if grouped.empty: return grouped
            
            # Use AnalyticsEngine for VMoy
            grouped['Vmoy'] = grouped.apply(lambda r: AnalyticsEngine.compute_weighted_speed([r[c] for c in bin_cols], speed_centers), axis=1)
            grouped['Débit'] = grouped[bin_cols].sum(axis=1)
            grouped['Vmoy'] = grouped['Vmoy'].round(1)
            return grouped[['Date', 'Heure'] + bin_cols + ['Vmoy', 'Débit']]

        # Write to Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df_meta.to_excel(writer, sheet_name='Métadonnées', index=False)
            df_s1.to_excel(writer, sheet_name='Comptages Sens 1', index=False)
            df_s2.to_excel(writer, sheet_name='Comptages Sens 2', index=False)
            
            for d, c in [('Sens 1', 'VL'), ('Sens 2', 'VL'), ('Sens 1', 'PL'), ('Sens 2', 'PL')]:
                v_df = build_vitesse(d, c)
                if not v_df.empty:
                    v_df.to_excel(writer, sheet_name=f'Vitesse {d} {c}', index=False)
                    
        return file_path
