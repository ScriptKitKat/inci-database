"""Seed a lean, curated catalog of real, popular skincare products into Supabase.

Uses `match_ingredients_batch` to resolve every INCI token to an existing canonical
`ingredients` row (never auto-creating junk canonical rows).
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://xwdmtipxfgcxfemnizie.supabase.co").rstrip("/")

CURATED_PRODUCTS: list[dict[str, Any]] = [
    # --- CeraVe ---
    {
        "brand": "CeraVe",
        "name": "Hydrating Facial Cleanser",
        "short_description": "Gentle non-foaming daily cleanser with ceramides and hyaluronic acid for normal to dry skin.",
        "ingredients": [
            "Water", "Glycerin", "Cetearyl Alcohol", "PEG-40 Stearate", "Stearyl Alcohol",
            "Potassium Phosphate", "Ceramide NP", "Ceramide AP", "Ceramide EOP", "Carbomer",
            "Glyceryl Stearate", "Behentrimonium Methosulfate", "Sodium Lauroyl Lactylate",
            "Sodium Hyaluronate", "Cholesterol", "Phenoxyethanol", "Disodium EDTA",
            "Dipotassium Phosphate", "Tocopherol", "Phytosphingosine", "Xanthan Gum",
            "Cetyl Alcohol", "Polysorbate 20", "Ethylhexylglycerin",
        ],
    },
    {
        "brand": "CeraVe",
        "name": "Foaming Facial Cleanser",
        "short_description": "Refreshing gel-to-foam cleanser with niacinamide and ceramides for normal to oily skin.",
        "ingredients": [
            "Water", "Cocamidopropyl Hydroxysultaine", "Glycerin", "Sodium Lauroyl Sarcosinate",
            "Propanediol", "PEG-150 Pentaerythrityl Tetrastearate", "Niacinamide",
            "PEG-6 Caprylic/Capric Glycerides", "Sodium Methyl Cocoyl Taurate",
            "Propylene Glycol", "Ceramide NP", "Ceramide AP", "Ceramide EOP", "Carbomer",
            "Sodium Chloride", "Sodium Lauroyl Lactylate", "Cholesterol", "Phenoxyethanol",
            "Disodium EDTA", "Citric Acid", "Tetrasodium EDTA", "Hydrolyzed Hyaluronic Acid",
            "Phytosphingosine", "Xanthan Gum", "Ethylhexylglycerin",
        ],
    },
    {
        "brand": "CeraVe",
        "name": "Moisturizing Cream",
        "short_description": "Rich, fragrance-free barrier-repair cream with three essential ceramides and hyaluronic acid.",
        "ingredients": [
            "Water", "Glycerin", "Cetearyl Alcohol", "Caprylic/Capric Triglyceride",
            "Cetyl Alcohol", "Ceteareth-20", "Petrolatum", "Potassium Phosphate",
            "Ceramide NP", "Ceramide AP", "Ceramide EOP", "Carbomer", "Dimethicone",
            "Behentrimonium Methosulfate", "Sodium Lauroyl Lactylate", "Sodium Hyaluronate",
            "Cholesterol", "Phenoxyethanol", "Disodium EDTA", "Dipotassium Phosphate",
            "Tocopherol", "Phytosphingosine", "Xanthan Gum", "Polyglyceryl-3 Diisostearate",
            "Ethylhexylglycerin",
        ],
    },
    {
        "brand": "CeraVe",
        "name": "PM Facial Moisturizing Lotion",
        "short_description": "Ultra-lightweight oil-free night lotion with niacinamide, ceramides, and hyaluronic acid.",
        "ingredients": [
            "Water", "Glycerin", "Caprylic/Capric Triglyceride", "Niacinamide",
            "Cetearyl Alcohol", "Potassium Phosphate", "Ceramide NP", "Ceramide AP",
            "Ceramide EOP", "Carbomer", "Dimethicone", "Ceteareth-20",
            "Behentrimonium Methosulfate", "Sodium Lauroyl Lactylate", "Sodium Hyaluronate",
            "Cholesterol", "Phenoxyethanol", "Disodium EDTA", "Dipotassium Phosphate",
            "Caprylyl Glycol", "Phytosphingosine", "Xanthan Gum", "Polyglyceryl-3 Diisostearate",
            "Ethylhexylglycerin",
        ],
    },
    {
        "brand": "CeraVe",
        "name": "Renewing SA Cleanser",
        "short_description": "Exfoliating salicylic acid gel cleanser that smooths rough, bumpy skin without stripping.",
        "ingredients": [
            "Water", "Cocamidopropyl Hydroxysultaine", "Glycerin", "Sodium Lauroyl Sarcosinate",
            "Niacinamide", "Gluconolactone", "PEG-150 Pentaerythrityl Tetrastearate",
            "Sodium Methyl Cocoyl Taurate", "Zea Mays Oil", "Ceramide NP", "Ceramide AP",
            "Ceramide EOP", "Carbomer", "Calcium Gluconate", "Sodium Chloride",
            "Salicylic Acid", "Sodium Benzoate", "Sodium Lauroyl Lactylate", "Cholecalciferol",
            "Cholesterol", "Phenoxyethanol", "Disodium EDTA", "Tetrasodium EDTA",
            "Hydrolyzed Hyaluronic Acid", "Phytosphingosine", "Xanthan Gum", "Ethylhexylglycerin",
        ],
    },
    # --- La Roche-Posay ---
    {
        "brand": "La Roche-Posay",
        "name": "Toleriane Hydrating Gentle Cleanser",
        "short_description": "Milky, fragrance-free daily cleanser with niacinamide and ceramide-3 for sensitive dry skin.",
        "ingredients": [
            "Water", "Glycerin", "Pentaerythrityl Tetraethylhexanoate", "Propylene Glycol",
            "Ammonium Polyacryloyldimethyl Taurate", "Polysorbate 60", "Ceramide NP",
            "Niacinamide", "Sodium Chloride", "Coco-Betaine", "Disodium EDTA",
            "Caprylyl Glycol", "Panthenol", "Tocopherol",
        ],
    },
    {
        "brand": "La Roche-Posay",
        "name": "Toleriane Double Repair Face Moisturizer",
        "short_description": "Oil-free daily barrier moisturizer with ceramide-3, niacinamide, and glycerin.",
        "ingredients": [
            "Water", "Glycerin", "Dimethicone", "Hydrogenated Polyisobutene", "Niacinamide",
            "Ammonium Polyacryloyldimethyl Taurate", "Myristyl Myristate", "Stearic Acid",
            "Ceramide NP", "Potassium Cetyl Phosphate", "Isobutane", "Glyceryl Stearate SE",
            "Sodium Hydroxide", "Myristic Acid", "Palmitic Acid", "Capryloyl Glycine",
            "Caprylyl Glycol", "Xanthan Gum", "Tocopherol",
        ],
    },
    {
        "brand": "La Roche-Posay",
        "name": "Cicaplast Balm B5",
        "short_description": "Soothing multi-purpose barrier repair balm with 5% panthenol, madecassoside, and shea butter.",
        "ingredients": [
            "Water", "Hydrogenated Polyisobutene", "Dimethicone", "Glycerin",
            "Butyrospermum Parkii Butter", "Panthenol", "Propanediol", "Butylene Glycol",
            "Aluminum Starch Octenylsuccinate", "Cetyl PEG/PPG-10/1 Dimethicone",
            "Trihydroxystearin", "Zinc Gluconate", "Madecassoside", "Manganese Gluconate",
            "Silica", "Aluminum Hydroxide", "Magnesium Sulfate", "Disodium EDTA",
            "Copper Gluconate", "Capryloyl Glycine", "Citric Acid", "Acetylated Glycol Stearate",
            "Polyglyceryl-4 Isostearate", "Tocopherol", "Pentaerythrityl Tetra-Di-T-Butyl Hydroxyhydrocinnamate",
            "Titanium Dioxide",
        ],
    },
    {
        "brand": "La Roche-Posay",
        "name": "Anthelios Melt-in Milk Sunscreen SPF 60",
        "short_description": "Broad-spectrum face and body sunscreen with antioxidants for sensitive skin.",
        "ingredients": [
            "Avobenzone", "Homosalate", "Octisalate", "Octocrylene", "Water",
            "Styrene/Acrylates Copolymer", "Dimethicone", "Polymethylsilsesquioxane",
            "Butyloctyl Salicylate", "Glycerin", "Alcohol Denat.", "Poly C10-30 Alkyl Acrylate",
            "Caprylyl Methicone", "Trisiloxane", "Acrylates/Dimethicone Copolymer",
            "PEG-100 Stearate", "Potassium Cetyl Phosphate", "Propylene Glycol",
            "PEG-8 Laurate", "Phenoxyethanol", "Caprylyl Glycol", "Tocopherol",
            "Disodium EDTA", "Xanthan Gum",
        ],
    },
    # --- The Ordinary ---
    {
        "brand": "The Ordinary",
        "name": "Niacinamide 10% + Zinc 1%",
        "short_description": "High-strength vitamin B3 and zinc serum to visibly balance sebum and refine pores.",
        "ingredients": [
            "Water", "Niacinamide", "Pentylene Glycol", "Zinc PCA", "Dimethyl Isosorbide",
            "Tamarindus Indica Seed Gum", "Xanthan Gum", "Isoceteth-20", "Ethoxydiglycol",
            "Phenoxyethanol", "Chlorphenesin",
        ],
    },
    {
        "brand": "The Ordinary",
        "name": "Hyaluronic Acid 2% + B5",
        "short_description": "Multi-molecular hyaluronic acid hydrating serum with pro-vitamin B5 and ceramides.",
        "ingredients": [
            "Water", "Sodium Hyaluronate", "Propanediol", "Pentylene Glycol",
            "Hydrolyzed Hyaluronic Acid", "Sodium Hyaluronate Crosspolymer", "Phospholipids",
            "Sphingolipids", "Panthenol", "Ahnfeltiopsis Concinna Extract", "Glycerin",
            "Polysorbate 20", "Citric Acid", "Sodium Citrate", "p-Anisic Acid",
            "Tocopherol", "Trisodium Ethylenediamine Disuccinate", "Caprylyl Glycol",
            "Ethoxydiglycol", "Ethylhexylglycerin", "Hexylene Glycol", "Phenoxyethanol",
            "Chlorphenesin",
        ],
    },
    {
        "brand": "The Ordinary",
        "name": "Glycolic Acid 7% Exfoliating Toner",
        "short_description": "Daily alpha hydroxy acid resurfacing toner with Tasmanian pepperberry and aloe.",
        "ingredients": [
            "Water", "Glycolic Acid", "Rosa Damascena Flower Water", "Centaurea Cyanus Flower Water",
            "Aloe Barbadensis Leaf Water", "Propanediol", "Glycerin", "Triethanolamine",
            "Aminomethyl Propanol", "Panax Ginseng Root Extract", "Tasmannia Lanceolata Fruit/Leaf Extract",
            "Aspartic Acid", "Alanine", "Glycine", "Serine", "Valine", "Isoleucine",
            "Proline", "Threonine", "Histidine", "Phenylalanine", "Glutamic Acid", "Arginine",
            "PCA", "Sodium PCA", "Sodium Lactate", "Fructose", "Glucose", "Sucrose", "Urea",
            "Hexyl Nicotinate", "Dextrin", "Citric Acid", "Polysorbate 20", "Gellan Gum",
            "Trisodium Ethylenediamine Disuccinate", "Sodium Chloride", "Hexylene Glycol",
            "Potassium Sorbate", "Sodium Benzoate", "1,2-Hexanediol", "Caprylyl Glycol",
        ],
    },
    {
        "brand": "The Ordinary",
        "name": "Azelaic Acid Suspension 10%",
        "short_description": "Brightening cream-gel formula with 10% azelaic acid to even skin tone and texture.",
        "ingredients": [
            "Water", "Isodecyl Neopentanoate", "Dimethicone", "Azelaic Acid",
            "Dimethicone/Bis-Isobutyl PPG-20 Crosspolymer", "Dimethyl Isosorbide",
            "Hydroxyethyl Acrylate/Sodium Acryloyldimethyl Taurate Copolymer",
            "Polysilicone-11", "Isohexadecane", "Tocopherol", "Trisodium Ethylenediamine Disuccinate",
            "Isoceteth-20", "Polysorbate 60", "Triethanolamine", "Ethoxydiglycol",
            "Phenoxyethanol", "Chlorphenesin",
        ],
    },
    {
        "brand": "The Ordinary",
        "name": "100% Plant-Derived Squalane",
        "short_description": "Lightweight single-ingredient plant-derived squalane oil for hydration without heaviness.",
        "ingredients": ["Squalane"],
    },
    {
        "brand": "The Ordinary",
        "name": "Natural Moisturizing Factors + HA",
        "short_description": "Non-greasy surface hydration cream with amino acids, fatty acids, urea, and hyaluronic acid.",
        "ingredients": [
            "Water", "Caprylic/Capric Triglyceride", "Cetyl Alcohol", "Propanediol",
            "Stearyl Alcohol", "Glycerin", "Sodium Hyaluronate", "Arginine", "Aspartic Acid",
            "Glycine", "Alanine", "Serine", "Valine", "Isoleucine", "Proline", "Threonine",
            "Histidine", "Phenylalanine", "Glucose", "Maltose", "Fructose", "Trehalose",
            "Sodium PCA", "PCA", "Sodium Lactate", "Urea", "Allantoin", "Linoleic Acid",
            "Oleic Acid", "Phytosteryl Canola Glycerides", "Palmitic Acid", "Stearic Acid",
            "Lecithin", "Triolein", "Tocopherol", "Carbomer", "Isoceteth-20",
            "Polysorbate 60", "Sodium Chloride", "Citric Acid", "Trisodium Ethylenediamine Disuccinate",
            "Pentylene Glycol", "Triethanolamine", "Sodium Hydroxide", "Phenoxyethanol",
            "Chlorphenesin",
        ],
    },
    # --- Paula's Choice ---
    {
        "brand": "Paula's Choice",
        "name": "Skin Perfecting 2% BHA Liquid Exfoliant",
        "short_description": "Leave-on 2% salicylic acid liquid exfoliant to unclog pores and smooth texture.",
        "ingredients": [
            "Water", "Methylpropanediol", "Butylene Glycol", "Salicylic Acid",
            "Polysorbate 20", "Camellia Oleifera Leaf Extract", "Sodium Hydroxide",
            "Tetrasodium EDTA",
        ],
    },
    {
        "brand": "Paula's Choice",
        "name": "10% Azelaic Acid Booster",
        "short_description": "Multi-action brightening cream with 10% azelaic acid, 0.5% salicylic acid, and licorice root.",
        "ingredients": [
            "Water", "Azelaic Acid", "C12-15 Alkyl Benzoate", "Caprylic/Capric Triglyceride",
            "Methyl Glucose Sesquistearate", "Glycerin", "Cetearyl Alcohol", "Glyceryl Stearate",
            "Dimethicone", "Salicylic Acid", "Adenosine", "Glycyrrhiza Glabra Root Extract",
            "Boerhavia Diffusa Root Extract", "Allantoin", "Bisabolol", "Cyclopentasiloxane",
            "Xanthan Gum", "Sclerotium Gum", "Propanediol", "Butylene Glycol",
            "Phenoxyethanol",
        ],
    },
    # --- Cetaphil ---
    {
        "brand": "Cetaphil",
        "name": "Gentle Skin Cleanser",
        "short_description": "Mild, soap-free hydrating cleanser with niacinamide, panthenol, and glycerin.",
        "ingredients": [
            "Water", "Glycerin", "Cetearyl Alcohol", "Panthenol", "Niacinamide",
            "Pantolactone", "Xanthan Gum", "Sodium Cocoyl Isethionate", "Sodium Benzoate",
            "Citric Acid",
        ],
    },
    {
        "brand": "Cetaphil",
        "name": "Moisturizing Lotion",
        "short_description": "Lightweight everyday lotion with avocado oil, niacinamide, and vitamin B5.",
        "ingredients": [
            "Water", "Glycerin", "Isopropyl Palmitate", "Cetearyl Alcohol", "Ceteareth-20",
            "Panthenol", "Niacinamide", "Tocopheryl Acetate", "Dimethicone",
            "Persea Gratissima Oil", "Helianthus Annuus Seed Oil", "Pantolactone",
            "Glyceryl Stearate", "Sodium Benzoate", "Benzyl Alcohol", "Citric Acid",
        ],
    },
    # --- Vanicream ---
    {
        "brand": "Vanicream",
        "name": "Gentle Facial Cleanser",
        "short_description": "Ultra-minimalist, fragrance-free cleanser formulated for highly sensitive and reactive skin.",
        "ingredients": [
            "Water", "Glycerin", "Coco-Glucoside", "Sodium Cocoyl Glycinate",
            "Acrylates Copolymer", "Caprylyl Glycol", "Mica", "Sodium Chloride",
            "1,2-Hexanediol", "Polyquaternium-7", "Sodium Hydroxide", "Tetrasodium EDTA",
        ],
    },
    {
        "brand": "Vanicream",
        "name": "Daily Facial Moisturizer",
        "short_description": "Fragrance-free lightweight moisturizer with squalane, hyaluronic acid, and five ceramides.",
        "ingredients": [
            "Water", "Squalane", "Glycerin", "Polyglyceryl-2 Stearate", "Glyceryl Stearate",
            "Stearyl Alcohol", "Hyaluronic Acid", "Ceramide EOP", "Ceramide NG",
            "Ceramide NP", "Ceramide AS", "Ceramide AP", "Carnosine", "Cholesterol",
            "Phytosterols", "Caprylyl Glycol", "Polyacrylate Crosspolymer-11",
            "1,2-Hexanediol", "Caprylhydroxamic Acid",
        ],
    },
    # --- Neutrogena ---
    {
        "brand": "Neutrogena",
        "name": "Hydro Boost Water Gel",
        "short_description": "Oil-free cooling gel moisturizer powered by hyaluronic acid and glycerin.",
        "ingredients": [
            "Water", "Glycerin", "Dimethicone", "Cetearyl Olivate", "Sorbitan Olivate",
            "Sodium Hyaluronate", "Ethylhexylglycerin", "Dimethicone/Vinyl Dimethicone Crosspolymer",
            "Synthetic Beeswax", "Carbomer", "Dimethiconol", "Sodium Hydroxide",
            "C12-14 Pareth-12", "Phenoxyethanol", "Chlorphenesin",
        ],
    },
    # --- Aveeno ---
    {
        "brand": "Aveeno",
        "name": "Calm + Restore Oat Gel Moisturizer",
        "short_description": "Fragrance-free gel cream with prebiotic oat and feverfew to calm sensitive, dry skin.",
        "ingredients": [
            "Water", "Glycerin", "Dimethicone", "Cetearyl Olivate", "Avena Sativa Kernel Flour",
            "Sorbitan Olivate", "Polyacrylamide", "Synthetic Beeswax", "Phenoxyethanol",
            "C13-14 Isoparaffin", "Butylene Glycol", "Dimethicone/Vinyl Dimethicone Crosspolymer",
            "Caprylyl Glycol", "Carbomer", "Chlorphenesin", "Dimethiconol", "Pentylene Glycol",
            "Chrysanthemum Parthenium Flower/Leaf/Stem Juice", "Ethylhexylglycerin",
            "Sodium Hydroxide", "Laureth-7", "Avena Sativa Kernel Extract",
            "Centella Asiatica Extract",
        ],
    },
    # --- COSRX ---
    {
        "brand": "COSRX",
        "name": "Advanced Snail 96 Mucin Power Essence",
        "short_description": "Hydrating and soothing essence with 96% snail secretion filtrate, panthenol, and allantoin.",
        "ingredients": [
            "Snail Secretion Filtrate", "Betaine", "Butylene Glycol", "1,2-Hexanediol",
            "Sodium Polyacrylate", "Phenoxyethanol", "Sodium Hyaluronate", "Allantoin",
            "Ethyl Hexanediol", "Carbomer", "Panthenol", "Arginine",
        ],
    },
    {
        "brand": "COSRX",
        "name": "Low pH Good Morning Gel Cleanser",
        "short_description": "Mildly acidic daily gel cleanser with tea tree leaf oil and betaine salicylate.",
        "ingredients": [
            "Water", "Cocamidopropyl Betaine", "Sodium Lauroyl Methyl Isethionate",
            "Polysorbate 20", "Styrax Japonicus Branch/Fruit/Leaf Extract", "Butylene Glycol",
            "Saccharomyces Ferment", "Cryptomeria Japonica Leaf Extract", "Nelumbo Nucifera Leaf Extract",
            "Pinus Palustris Leaf Extract", "Ulmus Davidiana Root Extract",
            "Oenothera Biennis Flower Extract", "Pueraria Lobata Root Extract",
            "Melaleuca Alternifolia Leaf Oil", "Allantoin", "Caprylyl Glycol",
            "Ethylhexylglycerin", "Betaine Salicylate", "Citric Acid", "Ethyl Hexanediol",
            "1,2-Hexanediol", "Trisodium Ethylenediamine Disuccinate", "Sodium Benzoate",
            "Disodium EDTA",
        ],
    },
    {
        "brand": "COSRX",
        "name": "Advanced Snail 92 All In One Cream",
        "short_description": "Lightweight gel-cream with 92% snail mucin, adenosine, and hyaluronic acid for plump hydration.",
        "ingredients": [
            "Snail Secretion Filtrate", "Betaine", "Caprylic/Capric Triglyceride",
            "Cetearyl Olivate", "Sorbitan Olivate", "Cetearyl Alcohol", "Carbomer",
            "Arginine", "Dimethicone", "Sodium Polyacrylate", "Phenoxyethanol",
            "Sodium Hyaluronate", "Stearic Acid", "Allantoin", "Panthenol", "Xanthan Gum",
            "Ethyl Hexanediol", "Adenosine",
        ],
    },
    # --- Beauty of Joseon ---
    {
        "brand": "Beauty of Joseon",
        "name": "Relief Sun: Rice + Probiotics SPF50+ PA++++",
        "short_description": "Creamy, non-greasy organic UV sunscreen with 30% rice extract, niacinamide, and probiotics.",
        "ingredients": [
            "Water", "Oryza Sativa Extract", "Dibutyl Adipate", "Propanediol",
            "Diethylamino Hydroxybenzoyl Hexyl Benzoate", "Polymethylsilsesquioxane",
            "Ethylhexyl Triazone", "Niacinamide", "Methylene Bis-Benzotriazolyl Tetramethylbutylphenol",
            "Coco-Caprylate/Caprate", "Caprylyl Methicone", "Diethylhexyl Butamido Triazone",
            "Glycerin", "Butylene Glycol", "Oryza Sativa Germ Extract",
            "Camellia Sinensis Leaf Extract", "Lactobacillus/Pumpkin Ferment Extract",
            "Bacillus/Soybean Ferment Extract", "Saccharum Officinarum Extract",
            "Macrocystis Pyrifera Extract", "Cocos Nucifera Fruit Extract",
            "Panax Ginseng Root Extract", "Monascus/Rice Ferment", "Pentylene Glycol",
            "Behenyl Alcohol", "Poly C10-30 Alkyl Acrylate", "Polyglyceryl-3 Methylglucose Distearate",
            "Decyl Glucoside", "Tromethamine", "Carbomer", "Acrylates/C10-30 Alkyl Acrylate Crosspolymer",
            "1,2-Hexanediol", "Sodium Stearoyl Glutamate", "Polyacrylate Crosspolymer-6",
            "Ethylhexylglycerin", "Adenosine", "Xanthan Gum", "Tocopherol",
        ],
    },
    {
        "brand": "Beauty of Joseon",
        "name": "Glow Serum: Propolis + Niacinamide",
        "short_description": "Honey-like brightening and soothing serum with 60% propolis extract and 2% niacinamide.",
        "ingredients": [
            "Propolis Extract", "Dipropylene Glycol", "Glycerin", "Butylene Glycol",
            "Water", "Niacinamide", "1,2-Hexanediol", "Melia Azadirachta Flower Extract",
            "Melia Azadirachta Leaf Extract", "Sodium Hyaluronate", "Curcuma Longa Root Extract",
            "Ocimum Sanctum Leaf Extract", "Theobroma Cacao Seed Extract",
            "Melaleuca Alternifolia Extract", "Centella Asiatica Extract",
            "Corallina Officinalis Extract", "Lotus Corniculatus Seed Extract",
            "Calophyllum Inophyllum Seed Oil", "Betaine Salicylate", "Sodium Polyacryloyldimethyl Taurate",
            "Tromethamine", "Polyglyceryl-10 Laurate", "Caprylyl Glycol", "Ethylhexylglycerin",
            "Dextrin", "Pentylene Glycol", "Octanediol", "Tocopherol", "Xanthan Gum", "Carbomer",
        ],
    },
    # --- Laneige ---
    {
        "brand": "Laneige",
        "name": "Cream Skin Cerapeptide Toner & Moisturizer",
        "short_description": "Milky 2-in-1 ceramide and peptide toner that delivers cream-level hydration.",
        "ingredients": [
            "Water", "Butylene Glycol", "Glycerin", "Limnanthes Alba Seed Oil",
            "Isopentyldiol", "1,2-Hexanediol", "Squalane", "Polyglyceryl-10 Stearate",
            "Glyceryl Stearate Citrate", "Sodium Stearoyl Glutamate", "Inulin Lauryl Carbamate",
            "Glyceryl Caprylate", "Ethylhexylglycerin", "Propanediol", "Disodium EDTA",
            "Carbomer", "Mannitol", "Acrylates/Stearyl Methacrylate Copolymer",
            "Tremella Fuciformis Sporocarp Extract", "Hyaluronic Acid", "Camellia Sinensis Leaf Extract",
            "Xanthan Gum", "Ceramide NP", "Camellia Japonica Flower Extract", "Tocopherol",
            "Acetyl Tetrapeptide-11",
        ],
    },
    {
        "brand": "Laneige",
        "name": "Lip Sleeping Mask Berry",
        "short_description": "Overnight nourishing lip mask with shea butter, murumuru butter, and vitamin C.",
        "ingredients": [
            "Diisostearyl Malate", "Hydrogenated Polyisobutene", "Phytosteryl/Isostearyl/Cetyl/Stearyl/Behenyl Dimer Dilinoleate",
            "Hydrogenated Poly(C6-14 Olefin)", "Polybutene", "Microcrystalline Wax",
            "Butyrospermum Parkii Butter", "Synthetic Wax", "Ethylene/Propylene/Styrene Copolymer",
            "Sucrose Tetrastearate Triacetate", "Mica", "Euphorbia Cerifera Wax",
            "Astrocaryum Murumuru Seed Butter", "Titanium Dioxide", "Parfum",
            "Glyceryl Caprylate", "Polyglyceryl-2 Diisostearate", "Butylene/Ethylene/Styrene Copolymer",
            "Copernicia Cerifera Wax", "Methicone", "Polyglyceryl-2 Triisostearate",
            "Cocos Nucifera Oil", "Pentaerythrityl Tetra-Di-T-Butyl Hydroxyhydrocinnamate",
            "Ascorbic Acid", "Water", "Glycerin", "Propanediol", "BHT",
            "Punica Granatum Fruit Juice", "Rubus Idaeus Juice", "Vitis Vinifera Juice",
        ],
    },
    # --- Hada Labo ---
    {
        "brand": "Hada Labo",
        "name": "Gokujyun Premium Hydrating Lotion",
        "short_description": "Rich Japanese hydrating toner with multiple molecular weights of hyaluronic acid.",
        "ingredients": [
            "Water", "Butylene Glycol", "Hydroxyethyl Urea", "Pentylene Glycol", "PPG-10 Methyl Glucose Ether",
            "Dipropylene Glycol", "Diglycerin", "Sodium Hyaluronate", "Hydrolyzed Hyaluronic Acid",
            "Sodium Acetylated Hyaluronate", "Hydroxypropyltrimonium Hyaluronate",
            "Sodium Hyaluronate Crosspolymer", "Aphanothece Sacrum Polysaccharides",
            "Hydrogenated Starch Hydrolysate", "Glycosyl Trehalose", "Sorbitol",
            "Triethyl Citrate", "PEG-32", "Carbomer", "PEG-75", "Succinic Acid",
            "Propanediol", "Diethoxyethyl Succinate", "Potassium Hydroxide", "Disodium Succinate",
            "Polyquaternium-51", "Caprylhydroxamic Acid", "Hydroxyethylcellulose", "Xanthan Gum",
            "Phenoxyethanol",
        ],
    },
    # --- Bioderma ---
    {
        "brand": "Bioderma",
        "name": "Sensibio H2O Micellar Water",
        "short_description": "Iconic fragrance-free micellar makeup remover formulated for sensitive skin.",
        "ingredients": [
            "Water", "PEG-6 Caprylic/Capric Glycerides", "Fructooligosaccharides", "Mannitol",
            "Xylitol", "Rhamnose", "Cucumis Sativus Fruit Extract", "Propylene Glycol",
            "Cetrimonium Bromide", "Disodium EDTA",
        ],
    },
    # --- EltaMD ---
    {
        "brand": "EltaMD",
        "name": "UV Clear Broad-Spectrum SPF 46",
        "short_description": "Oil-free mineral-hybrid sunscreen with zinc oxide, 5% niacinamide, and hyaluronic acid.",
        "ingredients": [
            "Zinc Oxide", "Octinoxate", "Water", "Cyclopentasiloxane", "Niacinamide",
            "Octyldodecyl Neopentanoate", "Hydroxyethyl Acrylate/Sodium Acryloyldimethyl Taurate Copolymer",
            "Polyisobutene", "PEG-7 Trimethylolpropane Coconut Ether", "Sodium Hyaluronate",
            "Tocopheryl Acetate", "Lactic Acid", "Oleth-3 Phosphate", "Phenoxyethanol",
            "Butylene Glycol", "Iodopropynyl Butylcarbamate", "Triethoxycaprylylsilane",
        ],
    },
    # --- Supergoop! ---
    {
        "brand": "Supergoop!",
        "name": "Unseen Sunscreen SPF 40",
        "short_description": "Weightless, invisible, scentless gel sunscreen that doubles as a makeup primer.",
        "ingredients": [
            "Avobenzone", "Homosalate", "Octisalate", "Octocrylene", "Isododecane",
            "Dimethicone Crosspolymer", "Dimethicone/Bis-Isobutyl PPG-20 Crosspolymer",
            "Polymethylsilsesquioxane", "Isohexadecane", "Dicaprylyl Carbonate",
            "Meadowfoam Estolide", "Caprylic/Capric Triglyceride", "Polyester-7",
            "Neopentyl Glycol Diheptanoate", "Lithothamnion Calcareum Extract",
            "Caprylyl Glycol", "Butyrospermum Parkii Butter", "Jojoba Esters",
            "Mannitol", "Boswellia Serrata Resin Extract", "Lecithin",
            "Microcrystalline Cellulose", "Diatomaceous Earth", "Zinc Sulfate", "Silica",
            "Tocopherol",
        ],
    },
    # --- First Aid Beauty ---
    {
        "brand": "First Aid Beauty",
        "name": "Ultra Repair Cream",
        "short_description": "Whipped barrier-soothing moisturizer with colloidal oatmeal, shea butter, and ceramide NP.",
        "ingredients": [
            "Water", "Stearic Acid", "Glycerin", "C12-15 Alkyl Benzoate", "Caprylic/Capric Triglyceride",
            "Glyceryl Stearate", "Glyceryl Stearate SE", "Cetearyl Alcohol", "Butyrospermum Parkii Butter",
            "Dimethicone", "Squalane", "Colloidal Oatmeal", "Allantoin", "Camellia Sinensis Leaf Extract",
            "Chrysanthemum Parthenium Extract", "Glycyrrhiza Glabra Root Extract", "Ceramide NP",
            "Caprylyl Glycol", "Phenoxyethanol", "Xanthan Gum", "Sodium Hydroxide", "Tetrasodium EDTA",
            "Eucalyptus Globulus Leaf Oil",
        ],
    },
    # --- The INKEY List ---
    {
        "brand": "The INKEY List",
        "name": "Oat Cleansing Balm",
        "short_description": "Nourishing oil-based cleansing balm with oat kernel oil and colloidal oatmeal.",
        "ingredients": [
            "Prunus Amygdalus Dulcis Oil", "Cetearyl Alcohol", "PEG-6 Caprylic/Capric Glycerides",
            "Avena Sativa Kernel Oil", "Candelilla Cera", "Silica", "Sorbitan Stearate",
            "Tribehenin", "PEG-60 Almond Glycerides", "Avena Sativa Kernel Flour",
            "Water", "Benzyl Alcohol", "Phenoxyethanol", "Lecithin", "1,2-Hexanediol",
            "Ascorbyl Palmitate", "Tocopherol", "Biosaccharide Gum-4", "Helianthus Annuus Seed Oil",
        ],
    },
    {
        "brand": "The INKEY List",
        "name": "Retinol Anti-Aging Serum",
        "short_description": "Slow-release stabilized retinol serum with squalane to smooth fine lines gently.",
        "ingredients": [
            "Water", "Glycerin", "Butylene Glycol", "Propanediol", "Dicaprylyl Carbonate",
            "Dimethicone", "Hydroxyethyl Acrylate/Sodium Acryloyldimethyl Taurate Copolymer",
            "Caprylyl Glycol", "Phospholipids", "Caprylic/Capric Glycerides", "Squalane",
            "Dimethyl Isosorbide", "Glycine Soja Extract", "Carbomer", "Sodium Ascorbate",
            "Tocopherol", "Polysorbate 60", "Tocopheryl Acetate", "Glycolipids",
            "Sodium Hydroxide", "Disodium EDTA", "Hydroxypinacolone Retinoate", "Retinol",
            "Glycine Soja Sterols", "Leuconostoc/Radish Root Ferment Filtrate", "PEG-40 Hydrogenated Castor Oil",
            "Hyaluronic Acid", "Polysorbate 20", "Palmitoyl Tetrapeptide-7", "Palmitoyl Tripeptide-1",
            "Phenoxyethanol",
        ],
    },
    # --- Naturium ---
    {
        "brand": "Naturium",
        "name": "Niacinamide Cleansing Gelee 3%",
        "short_description": "Gentle gel cleanser with 3% niacinamide, hyaluronic acid, and vitamin C.",
        "ingredients": [
            "Water", "Glycerin", "Sodium Cocoyl Glutamate", "Niacinamide",
            "Acrylates Copolymer", "Cocamidopropyl Hydroxysultaine", "Sodium Cocoamphoacetate",
            "Caprylyl/Capryl Glucoside", "Sodium Hyaluronate", "Sodium Ascorbyl Phosphate",
            "Tocopherol", "Xanthan Gum", "Citric Acid", "Sodium Chloride",
            "Ethylhexylglycerin", "Phenoxyethanol",
        ],
    },
    {
        "brand": "Naturium",
        "name": "Tranexamic Topical Acid 5%",
        "short_description": "Dark-spot targeting serum with 5% tranexamic acid, kojic acid, niacinamide, and licorice.",
        "ingredients": [
            "Water", "Propanediol", "Tranexamic Acid", "Niacinamide", "Butylene Glycol",
            "Glycerin", "Kojic Acid", "Glycyrrhiza Glabra Root Extract", "Tocopherol",
            "Caprylyl Glycol", "Xanthan Gum", "Citric Acid", "Phenoxyethanol",
            "Ethylhexylglycerin",
        ],
    },
    # --- Good Molecules ---
    {
        "brand": "Good Molecules",
        "name": "Discoloration Correcting Serum",
        "short_description": "Daily brightening serum formulated with tranexamic acid and 4% niacinamide.",
        "ingredients": [
            "Water", "Butylene Glycol", "Propanediol", "Glycerin", "Niacinamide",
            "Cetyl Tranexamate Mesylate", "Ceteth-20", "Citric Acid", "Tocopherol",
            "Polyacrylate Crosspolymer-6", "Phenoxyethanol", "Ethylhexylglycerin",
            "Trisodium Ethylenediamine Disuccinate",
        ],
    },
    # --- Byoma ---
    {
        "brand": "Byoma",
        "name": "Moisturizing Gel-Cream",
        "short_description": "Oil-free barrier-boosting gel-cream with tri-ceramide complex, niacinamide, and green tea.",
        "ingredients": [
            "Water", "Glycerin", "Caprylic/Capric Triglyceride", "Pentaerythrityl Tetraethylhexanoate",
            "Polyglyceryl-3 Methylglucose Distearate", "Niacinamide", "Ceramide NP",
            "Cholesterol", "Phytosphingosine", "Camellia Sinensis Leaf Extract",
            "Stearic Acid", "Oleic Acid", "Lactic Acid", "Hydrogenated Lecithin",
            "Cetearyl Alcohol", "Panthenol", "Carbomer", "Xanthan Gum", "Tromethamine",
            "1,2-Hexanediol", "Caprylyl Glycol", "Hydroxyacetophenone",
        ],
    },
    # --- Rhode ---
    {
        "brand": "Rhode",
        "name": "Glazing Milk",
        "short_description": "Nutrient-rich milky essence with ceramides, beta-glucan, and magnesium-zinc-copper complex.",
        "ingredients": [
            "Water", "C12-15 Alkyl Benzoate", "Coconut Alkanes", "Glycerin", "Polyglyceryl-3 Oleate",
            "Polyglyceryl-10 Mono/Dioleate", "Tocopherol", "Sodium Hyaluronate", "Ceramide NP",
            "Ceramide AP", "Ceramide EOP", "Beta-Glucan", "Copper Gluconate",
            "Magnesium Aspartate", "Zinc Gluconate", "Sodium Phytate", "Xanthan Gum",
            "Sclerotium Gum", "Lecithin", "Pullulan", "Silica", "Sodium Hydroxide",
            "Citric Acid", "Phenoxyethanol", "Ethylhexylglycerin",
        ],
    },
    # --- Tower 28 ---
    {
        "brand": "Tower 28",
        "name": "SOS Daily Rescue Facial Spray",
        "short_description": "Minimalist 3-ingredient hypochlorous acid mist to calm redness and stressed skin.",
        "ingredients": ["Water", "Sodium Chloride", "Hypochlorous Acid"],
    },
    # --- SkinCeuticals ---
    {
        "brand": "SkinCeuticals",
        "name": "C E Ferulic",
        "short_description": "Antioxidant vitamin C serum combining 15% L-ascorbic acid, 1% vitamin E, and 0.5% ferulic acid.",
        "ingredients": [
            "Water", "Ethoxydiglycol", "Ascorbic Acid", "Glycerin", "Propylene Glycol",
            "Laureth-23", "Phenoxyethanol", "Tocopherol", "Triethanolamine", "Ferulic Acid",
            "Panthenol", "Sodium Hyaluronate",
        ],
    },
    # --- Differin ---
    {
        "brand": "Differin",
        "name": "Adapalene Gel 0.1% Acne Treatment",
        "short_description": "Dermatologist-developed OTC retinoid gel with 0.1% adapalene for acne-prone skin.",
        "ingredients": [
            "Adapalene", "Carbomer", "Disodium EDTA", "Methylparaben", "Poloxamer 182",
            "Propylene Glycol", "Water", "Sodium Hydroxide",
        ],
    },
    # --- PanOxyl ---
    {
        "brand": "PanOxyl",
        "name": "Acne Creamy Wash 4% Benzoyl Peroxide",
        "short_description": "Daily antimicrobial acne cleanser with 4% benzoyl peroxide and moisturizing humectants.",
        "ingredients": [
            "Benzoyl Peroxide", "Water", "Glycerin", "Cetearyl Alcohol", "Cetyl Alcohol",
            "Dimethicone", "Mineral Oil", "Petrolatum", "Potassium Lauryl Sulfate",
            "Propylene Glycol", "Sodium PCA", "Stearyl Alcohol", "Xanthan Gum",
            "Lactic Acid", "Citric Acid", "Imidazolidinyl Urea",
        ],
    },
    # --- Drunk Elephant ---
    {
        "brand": "Drunk Elephant",
        "name": "Protini Polypeptide Cream",
        "short_description": "Protein-rich moisturizer with signal peptides, amino acids, and pygmy waterlily.",
        "ingredients": [
            "Water", "Dicaprylyl Carbonate", "Glycerin", "Cetearyl Alcohol", "Cetearyl Olivate",
            "Sorbitan Olivate", "Sclerocarya Birrea Seed Oil", "Bacillus/Folic Acid Ferment Filtrate Extract",
            "Nymphaea Alba Root Extract", "sh-Oligopeptide-1", "sh-Oligopeptide-2",
            "sh-Polypeptide-1", "sh-Polypeptide-9", "sh-Polypeptide-11", "Copper Palmitoyl Heptapeptide-14",
            "Heptapeptide-15 Palmitate", "Palmitoyl Tetrapeptide-7", "Palmitoyl Tripeptide-1",
            "Alanine", "Arginine", "Glycine", "Histidine", "Isoleucine", "Phenylalanine",
            "Proline", "Serine", "Threonine", "Valine", "Acetyl Glutamine",
            "Coconut Alkanes", "Coco-Caprylate/Caprate", "Sodium Hyaluronate", "Aspartic Acid",
            "Linoleic Acid", "Linolenic Acid", "Lecithin", "Butylene Glycol",
            "Polyvinyl Alcohol", "Sodium Lactate", "Sodium PCA", "PCA", "Sorbitan Isostearate",
            "Carbomer", "Polysorbate 20", "Polysorbate 60", "Lactic Acid/Glycolic Acid Copolymer",
            "Hydroxyethyl Acrylate/Sodium Acryloyldimethyl Taurate Copolymer", "Xanthan Gum",
            "Isomalt", "1,2-Hexanediol", "Caprylyl Glycol", "Chlorphenesin", "Phenoxyethanol",
            "Tocopherol", "Sodium Benzoate", "Phenylpropanol", "Glyceryl Caprylate",
            "Symbiosis",
        ],
    },
    # --- Kiehl's ---
    {
        "brand": "Kiehl's",
        "name": "Ultra Facial Cream",
        "short_description": "24-hour daily hydrating cream with olive-derived squalane and glacial glycoprotein.",
        "ingredients": [
            "Water", "Glycerin", "Dimethicone", "Squalane", "Bis-PEG-18 Methyl Ether Dimethyl Silane",
            "Sucrose Stearate", "Stearyl Alcohol", "PEG-8 Stearate", "Myristyl Myristate",
            "Prunus Armeniaca Kernel Oil", "Phenoxyethanol", "Persea Gratissima Oil",
            "Glyceryl Stearate", "Cetyl Alcohol", "Oryza Sativa Bran Oil",
            "Olea Europaea Fruit Oil", "Chlorphenesin", "Stearic Acid", "Palmitic Acid",
            "Carbomer", "Acrylates/C10-30 Alkyl Acrylate Crosspolymer", "Prunus Amygdalus Dulcis Oil",
            "Xanthan Gum", "Ethylhexylglycerin", "Sodium Hydroxide", "Tocopherol",
            "Glycine Soja Oil", "Pseudoalteromonas Ferment Extract", "Myristic Acid",
            "Hydroxypalmitoyl Sphinganine", "Salicylic Acid", "Citric Acid",
        ],
    },
    # --- Youth to the People ---
    {
        "brand": "Youth to the People",
        "name": "Superfood Cleanser",
        "short_description": "Antioxidant gel cleanser with kale, spinach, and green tea extracts.",
        "ingredients": [
            "Water", "Cocamidopropyl Hydroxysultaine", "Sodium Cocoyl Glutamate",
            "Aloe Barbadensis Leaf Juice", "Sorbeth-230 Tetraoleate", "Polysorbate 20",
            "Brassica Oleracea Acephala Leaf Extract", "Spinacia Oleracea Leaf Extract",
            "Camellia Sinensis Leaf Extract", "Medicago Sativa Extract", "Chamomilla Recutita Flower Extract",
            "Tetrahexyldecyl Ascorbate", "Glycerin", "Panthenol", "Tocopheryl Acetate",
            "Decyl Glucoside", "Sorbitan Laurate", "Tetrasodium Glutamate Diacetate",
            "Gluconolactone", "Calcium Gluconate", "Ethylhexylglycerin", "Maltodextrin",
            "Citric Acid", "Phenoxyethanol", "Potassium Sorbate", "Sodium Benzoate",
        ],
    },
    # --- Tatcha ---
    {
        "brand": "Tatcha",
        "name": "The Dewy Skin Cream",
        "short_description": "Rich plumping moisturizer with Japanese purple rice, squalane, and botanical extracts.",
        "ingredients": [
            "Water", "Saccharomyces/Rice Ferment Filtrate", "Glycerin", "Propanediol",
            "Dimethicone", "Squalane", "Diisostearyl Malate", "Behenyl Alcohol",
            "Myristyl Myristate", "Dipentaerythrityl Hexahydroxystearate", "Bis-Diglyceryl Polyacyladipate-2",
            "Tridecyl Trimellitate", "Inositol", "Sorbitan Tristearate", "Beheneth-20",
            "Camellia Sinensis Leaf Extract", "Cladosiphon Okamuranus Extract",
            "Chondrus Crispus Extract", "Betaphycus Gelatinum Extract", "Oryza Sativa Bran Extract",
            "Panax Ginseng Root Extract", "Origanum Majorana Leaf Extract", "Thymus Serpyllum Extract",
            "Malva Sylvestris Flower Extract", "Sodium Hyaluronate", "Gold", "Sericin",
            "Phytosteryl Macadamiate", "Tocopherol", "Hydroxyethyl Acrylate/Sodium Acryloyldimethyl Taurate Copolymer",
            "Sorbitan Isostearate", "Polysorbate 60", "Butylene Glycol", "Dimethicone/Vinyl Dimethicone Crosspolymer",
            "Sodium Benzoate", "Phenoxyethanol", "Ethylhexylglycerin", "Parfum",
        ],
    },
    # --- Round Lab ---
    {
        "brand": "Round Lab",
        "name": "Birch Juice Moisturizing Sunscreen SPF50+ PA++++",
        "short_description": "Hydrating Korean chemical sunscreen with birch sap, niacinamide, and hyaluronic acid.",
        "ingredients": [
            "Water", "Dibutyl Adipate", "Propanediol", "Diethylamino Hydroxybenzoyl Hexyl Benzoate",
            "Polymethylsilsesquioxane", "Ethylhexyl Triazone", "Niacinamide",
            "Methylene Bis-Benzotriazolyl Tetramethylbutylphenol", "Coco-Caprylate/Caprate",
            "Caprylyl Methicone", "Diethylhexyl Butamido Triazone", "Glycerin",
            "1,2-Hexanediol", "Butylene Glycol", "Betula Platyphylla Japonica Juice",
            "Sodium Hyaluronate", "Hyaluronic Acid", "Glyceryl Glucoside", "Dipotassium Glycyrrhizate",
            "Allantoin", "Portulaca Oleracea Extract", "Artemisia Annua Extract",
            "Pinus Sylvestris Leaf Oil", "Anthemis Nobilis Flower Oil",
            "Acrylates/C10-30 Alkyl Acrylate Crosspolymer", "Sodium Stearoyl Glutamate",
            "Polyacrylate Crosspolymer-6", "Ethylhexylglycerin", "Ascorbic Acid",
            "Adenosine", "Pentylene Glycol", "Behenyl Alcohol", "Poly C10-30 Alkyl Acrylate",
            "Polyglyceryl-3 Methylglucose Distearate", "Decyl Glucoside", "Tromethamine",
            "Xanthan Gum", "Tocopherol",
        ],
    },
    # --- Torriden ---
    {
        "brand": "Torriden",
        "name": "DIVE-IN Low Molecular Hyaluronic Acid Serum",
        "short_description": "Refreshing 5D hyaluronic acid hydrating serum with panthenol, allantoin, and madecassoside.",
        "ingredients": [
            "Water", "Butylene Glycol", "Glycerin", "Dipropylene Glycol", "1,2-Hexanediol",
            "Panthenol", "Sodium Hyaluronate", "Hydrolyzed Hyaluronic Acid",
            "Sodium Acetylated Hyaluronate", "Sodium Hyaluronate Crosspolymer",
            "Hydrolyzed Sodium Hyaluronate", "Allantoin", "Trehalose", "Betaine",
            "Propanediol", "Portulaca Oleracea Extract", "Hamamelis Virginiana Extract",
            "Madecassoside", "Madecassic Acid", "Ceramide NP", "Beta-Glucan",
            "Malachite Extract", "Cholesterol", "Pentylene Glycol", "Glyceryl Acrylate/Acrylic Acid Copolymer",
            "PVM/MA Copolymer", "Polyglyceryl-10 Laurate", "Xanthan Gum", "Tromethamine",
            "Carbomer", "Ethylhexylglycerin", "Scutellaria Baicalensis Root Extract",
            "Paeonia Suffruticosa Root Extract",
        ],
    },
    # --- Anua ---
    {
        "brand": "Anua",
        "name": "Heartleaf 77% Soothing Toner",
        "short_description": "Calming watery toner with 77% houttuynia cordata extract, panthenol, and centella.",
        "ingredients": [
            "Houttuynia Cordata Extract", "Water", "1,2-Hexanediol", "Glycerin", "Betaine",
            "Panthenol", "Saccharum Officinarum Extract", "Portulaca Oleracea Extract",
            "Butylene Glycol", "Vitex Agnus-Castus Extract", "Chamomilla Recutita Flower Extract",
            "Arctium Lappa Root Extract", "Phellinus Linteus Extract", "Vitis Vinifera Fruit Extract",
            "Pyrus Malus Fruit Extract", "Centella Asiatica Extract", "Isopentyldiol",
            "Methylpropanediol", "Acrylates/C10-30 Alkyl Acrylate Crosspolymer", "Tromethamine",
            "Disodium EDTA",
        ],
    },
    # --- Eucerin ---
    {
        "brand": "Eucerin",
        "name": "Advanced Repair Cream",
        "short_description": "Rich fragrance-free moisturizer with urea, ceramide-3, and natural moisturizing factors.",
        "ingredients": [
            "Water", "Glycerin", "Urea", "Cetearyl Alcohol", "Hydrogenated Coco-Glycerides",
            "Octyldodecanol", "Caprylic/Capric Triglyceride", "Butyrospermum Parkii Butter",
            "Sodium Lactate", "Glyceryl Stearate SE", "Ceramide NP", "Lactic Acid",
            "Arginine", "Sodium PCA", "Cholesterol", "Helianthus Annuus Seed Oil",
            "Alanine", "Carnitine", "Glycine", "Sodium Chloride", "Dimethicone",
            "Tapioca Starch", "Chondrus Crispus Extract", "Sodium Cetearyl Sulfate",
            "Acrylates/C10-30 Alkyl Acrylate Crosspolymer", "Decylene Glycol", "Phenoxyethanol",
            "Pentylene Glycol",
        ],
    },
]


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "item"


def normalize_brand(text: str) -> str:
    return text.strip(" ").upper()


def req_json(key: str, method: str, path: str, body: Any = None, extra_headers: dict[str, str] | None = None) -> Any:
    headers = {"apikey": key, "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> {e.code}: {e.read().decode()}") from e


def main() -> int:
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not key:
        print("SUPABASE_SERVICE_ROLE_KEY is required", file=sys.stderr)
        return 1

    # 1. Collect all unique ingredient tokens across curated products and resolve in chunked batch RPCs
    all_tokens = sorted({tok for p in CURATED_PRODUCTS for tok in p["ingredients"]})
    token_to_ing: dict[str, str] = {}
    for i in range(0, len(all_tokens), 25):
        chunk = all_tokens[i : i + 25]
        resolved_rows = req_json(key, "POST", "rpc/match_ingredients_batch", {"inputs": chunk})
        for row in resolved_rows or []:
            if row.get("confidence", 0) >= 0.70:
                token_to_ing[row["input_token"]] = row["ingredient_id"]

    unmatched = [t for t in all_tokens if t not in token_to_ing]
    print(f"Resolved {len(token_to_ing)}/{len(all_tokens)} unique INCI tokens ({len(unmatched)} unmatched).")
    if unmatched:
        print("Unmatched tokens (skipped):", unmatched[:25])

    # 2. Upsert brands
    existing_brands = req_json(key, "GET", "brands?select=id,name,slug,normalized&limit=500") or []
    brand_by_norm = {b["normalized"]: b["id"] for b in existing_brands}

    created_brands = 0
    created_products = 0
    created_links = 0

    for prod in CURATED_PRODUCTS:
        b_name = prod["brand"]
        b_norm = normalize_brand(b_name)
        brand_id = brand_by_norm.get(b_norm)
        if not brand_id:
            res = req_json(
                key,
                "POST",
                "brands",
                {"name": b_name, "slug": slugify(b_name)},
                extra_headers={"Prefer": "return=representation"},
            )
            brand_id = res[0]["id"]
            brand_by_norm[b_norm] = brand_id
            created_brands += 1

        p_slug = slugify(f"{b_name}-{prod['name']}")
        existing = req_json(key, "GET", f"products?slug=eq.{urllib.parse.quote(p_slug)}&select=id") or []
        if existing:
            continue

        p_res = req_json(
            key,
            "POST",
            "products",
            {
                "name": prod["name"],
                "slug": p_slug,
                "brand_id": brand_id,
                "short_description": prod["short_description"],
            },
            extra_headers={"Prefer": "return=representation"},
        )
        product_id = p_res[0]["id"]
        created_products += 1

        seen_ing: set[str] = set()
        link_rows = []
        pos = 1
        for tok in prod["ingredients"]:
            ing_id = token_to_ing.get(tok)
            if not ing_id or ing_id in seen_ing:
                continue
            seen_ing.add(ing_id)
            link_rows.append({"product_id": product_id, "ingredient_id": ing_id, "position": pos})
            pos += 1
        if link_rows:
            req_json(key, "POST", "product_ingredients", link_rows)
            created_links += len(link_rows)

    print(f"Seeded {created_brands} brands, {created_products} products, {created_links} product_ingredients.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
