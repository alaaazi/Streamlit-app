import streamlit as st
import pandas as pd
import json
import requests
import io

st.set_page_config(page_title="Visualisation Promos Can-Am (API)", layout="wide")
st.title(" Promotions Can-Am Off-Road (API Live)")

API_URL = "https://can-am.brp.com/apps/sling/servlet/rest/digital-product-promotion.json?brand=canam-offroad&locale=en_US"

@st.cache_data
def fetch_api_data():
    response = requests.get(API_URL)
    response.raise_for_status()
    return response.json()

def flatten_json(data):
    rows = []
    for model in data.get("models", []):
        model_name = model.get("name")
        model_id = model.get("id")
        current_model_year = model.get("currentModelYear")
        for package in model.get("packages", []):
            package_name = package.get("name")
            package_id = package.get("id")
            price = package.get("price", {}).get("amount")
            currency = package.get("price", {}).get("currency")
            year = package.get("year")
            sku = package.get("sku")
            image = package.get("imageUrl")
            # Construction du lien image complet
            if image and not image.startswith("http"):
                image_full = "https://can-am.brp.com" + image
            else:
                image_full = image
            for offer in package.get("offers", []):
                offer_id = offer.get("id")
                offer_title = offer.get("title")
                start_date = offer.get("start_date")
                end_date = offer.get("end_date")
                promo_data = offer.get("promotion_data", {})
                promo_id = promo_data.get("promotion_id")
                promo_detail_id = promo_data.get("promotion_detail_id")
                regions = promo_data.get("regions", [])
                regions_str = ", ".join(regions) if regions else None

                if offer.get("offerDetails"):
                    for od in offer.get("offerDetails"):
                        offer_type = ",".join(od.get("offerDetailTypes", []))
                        # Tous les labels dans toutes les langues
                        all_labels = []
                        for label in od.get("labels", []):
                            key = f'[{label.get("languageCode")}-{label.get("countryCode")}:{label.get("labelType")}]'
                            val = label.get("text")
                            all_labels.append(f'{key} {val}')
                        labels_str = " | ".join(all_labels)
                        rows.append({
                            "currentModelYear": current_model_year,
                            "model_id": model_id,
                            "model_name": model_name,
                            "package_id": package_id,
                            "package_name": package_name,
                            "year": year,
                            "price": price,
                            "currency": currency,
                            "sku": sku,
                            "image_full_url": image_full,
                            "offer_id": offer_id,
                            "offer_title": offer_title,
                            "offer_type": offer_type,
                            "all_labels": labels_str,
                            "start_date": start_date,
                            "end_date": end_date,
                            "promotion_id": promo_id,
                            "promotion_detail_id": promo_detail_id,
                            "regions": regions_str
                        })
                else:
                    rows.append({
                        "currentModelYear": current_model_year,
                        "model_id": model_id,
                        "model_name": model_name,
                        "package_id": package_id,
                        "package_name": package_name,
                        "year": year,
                        "price": price,
                        "currency": currency,
                        "sku": sku,
                        "image_full_url": image_full,
                        "offer_id": offer_id,
                        "offer_title": offer_title,
                        "offer_type": None,
                        "all_labels": None,
                        "start_date": start_date,
                        "end_date": end_date,
                        "promotion_id": promo_id,
                        "promotion_detail_id": promo_detail_id,
                        "regions": regions_str
                    })
    return rows

if st.button("Charger les données depuis l’API Can-Am"):
    try:
        data = fetch_api_data()
        rows = flatten_json(data)
        df = pd.DataFrame(rows)

        with st.sidebar:
            st.subheader("Filtres")
            model_list = sorted(df["model_name"].dropna().unique())
            model_selected = st.multiselect("Modèle", model_list, default=model_list)
            package_list = sorted(df["package_name"].dropna().unique())
            package_selected = st.multiselect("Package", package_list, default=package_list)
            offer_types = sorted(df["offer_type"].dropna().unique())
            offer_type_selected = st.multiselect("Type d’offre", offer_types, default=offer_types)

        filtred = df[
            df["model_name"].isin(model_selected) &
            df["package_name"].isin(package_selected) &
            df["offer_type"].isin(offer_type_selected)
        ]

        st.markdown("### ")
        st.dataframe(filtred, use_container_width=True)

        st.markdown("---")
        # Correction ici : export Excel via buffer mémoire
        excel_buffer = io.BytesIO()
        filtred.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        st.download_button(
            label="Télécharger Excel filtré",
            data=excel_buffer,
            file_name="promos_canam_api.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")

else:
    st.info("Clique sur le bouton ci-dessus pour charger les données directement depuis l’API officielle Can-Am.")
