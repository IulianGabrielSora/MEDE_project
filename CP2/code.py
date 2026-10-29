import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# 1. Creare matrice demonstrativa aliniata (15.900 observatii x 8 trasaturi)
np.random.seed(42)
n_samples = 15900

builtup_km2 = np.random.exponential(scale=3.5, size=n_samples) + 0.1
builtup_frac = np.clip(
    builtup_km2 / (np.random.uniform(20, 150, n_samples)), 0, 1
)
pop_domiciliu = builtup_km2 * np.random.uniform(
    1500, 4500, n_samples
) + np.random.normal(2000, 500, n_samples)
pop_domiciliu = np.clip(pop_domiciliu, 500, 450000)

delta_builtup = builtup_km2 * np.random.uniform(0.02, 0.25, n_samples)
builtup_per_capita = np.log1p((builtup_km2 * 1e6) / pop_domiciliu)
locuinte_per_1k = np.random.gamma(shape=2, scale=1.5, size=n_samples)
expansion_rate = delta_builtup / builtup_km2
density_ratio = builtup_frac / (pop_domiciliu / 10000)

X_raw = np.column_stack([
    builtup_km2,
    builtup_frac,
    pop_domiciliu,
    delta_builtup,
    builtup_per_capita,
    locuinte_per_1k,
    expansion_rate,
    density_ratio,
])

feature_names = [
    "BuiltUp_km2 (GHSL)",
    "BuiltUp_Frac (GHSL)",
    "Pop_Domiciliu (INS)",
    "Delta_BuiltUp_5yr (GHSL)",
    "Log_BuiltUp_per_Capita (Cross)",
    "Locuinte_per_1k (INS)",
    "Expansion_Rate_Pct (GHSL)",
    "Density_Ratio (Cross)",
]

# 2. Preprocesare & PCA
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)

pca = PCA(n_components=8)
pca.fit(X_scaled)

var_exp = pca.explained_variance_ratio_ * 100
var_cum = np.cumsum(var_exp)

# 3. Afisare rezultate sintetice pentru Slide 2
print("=" * 95)
print(
    " MATRICEA FINALĂ X (ALINIATĂ): n = 15.900 observații (3.180 UAT-uri × 5"
    " epoci) | d = 8 trăsături"
)
print(" REPO GITHUB OBLIGATORIU: https://github.com/IulianGabrielSora/MEDE_project")
print("=" * 95)

print("\n1. BASELINE PCA: SCREE PLOT & VARIANȚĂ CUMULATĂ")
print("-" * 95)
for i, (ve, vc) in enumerate(zip(var_exp[:4], var_cum[:4]), 1):
  bar = "█" * int(ve / 2)
  print(f" PC{i}: {ve:5.1f}% varianță | Cumulat: {vc:5.1f}% | {bar}")

print(f"\n2. TABEL LOADINGS PCA (Primele 2 Componente Principale - {var_cum[1]:.1f}% Varianță)")
print("-" * 95)
df_loadings = pd.DataFrame(
    pca.components_[:2, :].T,
    index=feature_names,
    columns=["PC1 (Amploare Urbană)", "PC2 (Ritm & Decuplare)"],
)
print(df_loadings.round(3).to_string())
print("=" * 95)