"""
ROOTS & REFLECTANCE — my analysis of the Sentinel-2 NDVI/NDRE time series I export
from Earth Engine (see gee_extract_indices.js for how I pull the CSV).

Usage:
    python3 analyze.py path/to/roots_reflectance_ndvi_ndre.csv
    python3 analyze.py path/to/roots_reflectance_ndvi_ndre.csv path/to/roots_reflectance_sar.csv

The second argument is optional: the Sentinel-1 SAR export (see
gee_extract_sar.js). SAR isn't blocked by cloud cover, so when the optical
record is stuck (as it has been since 14 Jul 2026 — see DEVELOPMENT_LOG.md),
RVI still gives a cloud-proof read on canopy structure for that stretch. When
given, its dates are overlaid on the same chart as a dashed line rather than
folded into the NDVI numbers — RVI and NDVI aren't the same physical quantity,
so this is a second, independent check, not an interpolation of the first.

This gives me, in output/:
    - one NDVI+NDRE (and RVI, if given) time-series chart per field (7 charts)
    - one cross-field comparison chart per zone, grouped by crop mix
    - a combined summary CSV with a few derived stats (peak NDVI date, etc.)
"""
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

FIELD_LABELS = {
    ('sawardoh', 1): 'Sawardoh — Field 1 (Cotton & Tur)',
    ('sawardoh', 2): 'Sawardoh — Field 2 (Orange, Cotton & Tur)',
    ('sawardoh', 3): 'Sawardoh — Field 3 (Cotton)',
    ('sawardoh', 4): 'Sawardoh — Field 4 (Orange, Cotton, Tur & Turmeric)',
    ('sawardoh', 5): 'Sawardoh — Field 5 (Cotton)',
    ('karanja', 1): 'Karanja — Field 1 (Soyabean & Tur)',
    ('karanja', 2): 'Karanja — Field 2 (Soyabean)',
}


def load(csv_path):
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    # I noticed two adjacent Sentinel-2 orbit tiles sometimes both cover the same
    # field on the same date, giving two near-identical rows — I average those
    # down to one clean reading per field per date.
    static_cols = ['zone', 'field_num', 'field_id', 'name', 'area_ha', 'sown', 'crops']
    df = df.groupby(['zone', 'field_num', 'date'], as_index=False).agg(
        {**{c: 'first' for c in static_cols if c not in ('zone', 'field_num')},
         'NDVI': 'mean', 'NDRE': 'mean'}
    )
    df = df.sort_values(['zone', 'field_num', 'date'])
    return df


def load_sar(sar_csv_path):
    """Load the Sentinel-1 RVI export (see gee_extract_sar.js). Same duplicate-orbit
    averaging as the optical load(), kept as a separate function since SAR and
    optical extractions run independently and don't always share row shape."""
    df = pd.read_csv(sar_csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.groupby(['zone', 'field_num', 'date'], as_index=False).agg({'RVI': 'mean'})
    return df.sort_values(['zone', 'field_num', 'date'])


def plot_field(df, zone, field_num, out_dir, sar_df=None):
    sub = df[(df['zone'] == zone) & (df['field_num'] == field_num)]
    if sub.empty:
        print('No data for', zone, field_num)
        return
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(sub['date'], sub['NDVI'], marker='o', label='NDVI', color='#2e7d32')
    ax.plot(sub['date'], sub['NDRE'], marker='s', label='NDRE', color='#00838f')
    if sar_df is not None:
        sar_sub = sar_df[(sar_df['zone'] == zone) & (sar_df['field_num'] == field_num)]
        if not sar_sub.empty:
            # RVI is a different physical quantity from NDVI/NDRE — plotted dashed and
            # separately labelled so it reads as a second, independent check, not
            # another optical index on the same scale.
            ax.plot(sar_sub['date'], sar_sub['RVI'], marker='^', linestyle='--',
                     label='RVI (Sentinel-1 SAR, cloud-proof)', color='#c62828')
    ax.set_title(FIELD_LABELS.get((zone, field_num), f'{zone} field {field_num}'))
    ax.set_ylabel('Index value')
    ax.set_ylim(0, 1)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    out_path = os.path.join(out_dir, f'{zone}_field{field_num}_ndvi_ndre.png')
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print('Saved', out_path)


def plot_zone_comparison(df, zone, out_dir):
    sub = df[df['zone'] == zone]
    if sub.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    for field_num, grp in sub.groupby('field_num'):
        label = FIELD_LABELS.get((zone, field_num), f'Field {field_num}')
        ax.plot(grp['date'], grp['NDVI'], marker='o', label=label)
    ax.set_title(f'{zone.title()} — NDVI comparison across fields')
    ax.set_ylabel('NDVI')
    ax.set_ylim(0, 1)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    out_path = os.path.join(out_dir, f'{zone}_ndvi_comparison.png')
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print('Saved', out_path)


def summary_stats(df, out_dir):
    rows = []
    for (zone, field_num), grp in df.groupby(['zone', 'field_num']):
        peak = grp.loc[grp['NDVI'].idxmax()]
        rows.append({
            'zone': zone, 'field_num': field_num,
            'n_dates': len(grp),
            'first_date': grp['date'].min().date(),
            'last_date': grp['date'].max().date(),
            'peak_ndvi': round(peak['NDVI'], 3),
            'peak_ndvi_date': peak['date'].date(),
            'latest_ndvi': round(grp.iloc[-1]['NDVI'], 3),
            'latest_ndre': round(grp.iloc[-1]['NDRE'], 3),
        })
    out = pd.DataFrame(rows)
    out_path = os.path.join(out_dir, 'field_summary.csv')
    out.to_csv(out_path, index=False)
    print('Saved', out_path)
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    csv_path = sys.argv[1]
    sar_csv_path = sys.argv[2] if len(sys.argv) > 2 else None
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
    os.makedirs(out_dir, exist_ok=True)

    df = load(csv_path)
    sar_df = load_sar(sar_csv_path) if sar_csv_path else None
    if sar_df is not None:
        print(f'Loaded {len(sar_df)} SAR (RVI) rows from {sar_csv_path}')

    for zone, field_num in FIELD_LABELS:
        plot_field(df, zone, field_num, out_dir, sar_df=sar_df)
    for zone in ['sawardoh', 'karanja']:
        plot_zone_comparison(df, zone, out_dir)
    summary = summary_stats(df, out_dir)
    print(summary.to_string(index=False))


if __name__ == '__main__':
    main()
