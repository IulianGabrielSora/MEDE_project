import numpy as np
import pandas as pd
from sklearn.cross_decomposition import CCA
from sklearn.decomposition import PCA
from sklearn.manifold import trustworthiness
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler

# 1. Configurare reproducibilitate & subperioade (n = 15.900 = 3.180 UAT-uri x 5 epoci)
seeds = [42, 123, 456, 789, 2024]
np.random.seed(seeds[0])

n_uat = 3180
epochs = [2000, 2005, 2010, 2015, 2020]
n_samples = n_uat * len(epochs)
year_col = np.repeat(epochs, n_uat)

# Simulare date aliniate (inclusiv cele 6 sectoare Bucuresti ca UAT-uri LAU2 distincte)
builtup_km2 = np.random.exponential(scale=3.5, size=n_samples) + 0.1
builtup_frac = np.clip(builtup_km2 / np.random.uniform(20, 150, n_samples), 0, 1)
pop_domiciliu = builtup_km2 * np.random.uniform(1500, 4500, n_samples) + np.random.normal(2000, 500, n_samples)
pop_domiciliu = np.clip(pop_domiciliu, 500, 450000)

delta_builtup = builtup_km2 * np.random.uniform(0.02, 0.25, n_samples)
expansion_rate = delta_builtup / builtup_km2
locuinte_per_1k = np.random.gamma(shape=2, scale=1.5, size=n_samples)
log_builtup_pc = np.log1p((builtup_km2 * 1e6) / pop_domiciliu)
density_ratio = builtup_frac / (pop_domiciliu / 10000)

# Seturi pe surse: Sursa 1 (GHSL), Sursa 2 (INS), Combinat (GHSL + INS + Cross)
X_ghsl = np.column_stack([builtup_km2, builtup_frac, delta_builtup, expansion_rate])
X_ins = np.column_stack([pop_domiciliu, locuinte_per_1k])
X_comb = np.column_stack([
    builtup_km2, builtup_frac, pop_domiciliu, delta_builtup,
    log_builtup_pc, locuinte_per_1k, expansion_rate, density_ratio
])

# Esantion reprezentativ stratificat pentru calcul rapid Trustworthiness (n_sub = 3000)
def eval_pca(X, seeds_list):
    var_list, trust_list, mse_list = [], [], []
    for s in seeds_list:
        rng = np.random.RandomState(s)
        idx = rng.choice(len(X), size=3000, replace=False)
        Xs = StandardScaler().fit_transform(X[idx])
        pca = PCA(n_components=2, random_state=s)
        Z = pca.fit_transform(Xs)
        X_rec = pca.inverse_transform(Z)
        var_list.append(np.sum(pca.explained_variance_ratio_) * 100)
        trust_list.append(trustworthiness(Xs, Z, n_neighbors=10))
        mse_list.append(mean_squared_error(Xs, X_rec))
    return (
        f"{np.mean(var_list):.1f}%",
        f"{np.mean(trust_list):.3f} ± {np.std(trust_list):.3f}",
        f"{np.mean(mse_list):.3f} ± {np.std(mse_list):.3f}",
    )

def eval_cca(Xg, Xi, Xall, seeds_list):
    corr_list, trust_list, mse_list = [], [], []
    for s in seeds_list:
        rng = np.random.RandomState(s)
        idx = rng.choice(len(Xall), size=3000, replace=False)
        Xg_s = StandardScaler().fit_transform(Xg[idx])
        Xi_s = StandardScaler().fit_transform(Xi[idx])
        Xall_s = StandardScaler().fit_transform(Xall[idx])
        
        cca = CCA(n_components=2)
        U, V = cca.fit_transform(Xg_s, Xi_s)
        Z_cca = np.column_stack([U[:, 0], V[:, 0]])
        
        # Reconstructie liniara din spatiul canonic 2D
        W_rec = np.linalg.lstsq(Z_cca, Xall_s, rcond=None)[0]
        X_rec = Z_cca @ W_rec
        
        r1 = np.corrcoef(U[:, 0], V[:, 0])[0, 1]
        corr_list.append(r1)
        trust_list.append(trustworthiness(Xall_s, Z_cca, n_neighbors=10))
        mse_list.append(mean_squared_error(Xall_s, X_rec))
    return (
        f"r1={np.mean(corr_list):.2f} (can.)",
        f"{np.mean(trust_list):.3f} ± {np.std(trust_list):.3f}",
        f"{np.mean(mse_list):.3f} ± {np.std(mse_list):.3f}",
    )

# 2. Evaluare pe surse separate, combinate si pe subperioade
rows = []
v, t, m = eval_pca(X_ghsl, seeds)
rows.append(["PCA (Baseline)", "Sursa 1: GHSL (Satelit, d=4)", v, t, m])

v, t, m = eval_pca(X_ins, seeds)
rows.append(["PCA (Baseline)", "Sursa 2: INS (Statistică, d=2)", v, t, m])

v, t, m = eval_pca(X_comb, seeds)
rows.append(["PCA (Baseline)", "Combinat: GHSL + INS (d=8)", v, t, m])

v, t, m = eval_cca(X_ghsl, X_ins, X_comb, seeds)
rows.append(["CCA (Multi-View)", "Combinat: GHSL <-> INS (2D)", v, t, m])

# Stabilitate pe subperioade temporale (2000-2010 vs 2010-2020)
mask_p1 = year_col <= 2010
mask_p2 = year_col >= 2010
v1, t1, m1 = eval_cca(X_ghsl[mask_p1], X_ins[mask_p1], X_comb[mask_p1], seeds)
v2, t2, m2 = eval_cca(X_ghsl[mask_p2], X_ins[mask_p2], X_comb[mask_p2], seeds)

df_res = pd.DataFrame(
    rows,
    columns=["Metodă", "Domeniu Date", "Varianță / Corelație", "Trustworthiness (k=10)", "Eroare Reconstrucție (MSE)"]
)

print("=" * 105)
print(" CP3: COMPARAȚIE PCA (BASELINE) VS. CCA (MULTI-VIEW) | 5 SEED-URI (42, 123, 456, 789, 2024)")
print(" REPO GITHUB: https://github.com/IulianGabrielSora/MEDE_project")
print("=" * 105)
print(df_res.to_string(index=False))
print("-" * 105)
print(" STABILITATE PE SUBPERIOADE TEMPORALE (CCA Multi-View):")
print(f"  • Subperioada 2000–2010: {v1} | Trustworthiness = {t1} | MSE = {m1}")
print(f"  • Subperioada 2010–2020: {v2} | Trustworthiness = {t2} | MSE = {m2}")
print("=" * 105)