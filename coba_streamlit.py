import streamlit as st 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import datetime as dt

def convert_to_datetime(data):
    columns_to_convert = ['order_purchase_timestamp', 'order_approved_at']
    for column in columns_to_convert:
        data[column] = pd.to_datetime(data[column])
    return data

def total_order_per_month(data):
    data['year'] = data['order_purchase_timestamp'].dt.year
    data['month'] = data['order_purchase_timestamp'].dt.month

    filtered_data = data[data['year'].isin([2017, 2018])]

    monthly_data_analysis = filtered_data.groupby(['year', 'month']).agg({
        'order_id': 'nunique',
        'payment_value': 'sum'
    }).reset_index()

    monthly_data_analysis.rename(columns={
        'order_id': 'total_orders',
        'payment_value': 'total_payment'
    }, inplace=True)

    month_mapping = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'
    }

    monthly_data_analysis['month'] = monthly_data_analysis['month'].map(
        month_mapping)
    return monthly_data_analysis

all_df = pd.read_csv('./submission/dashboard/merge_all.csv')
all_df = convert_to_datetime(all_df)

total_order_per_months = total_order_per_month(all_df)

st.title('Proyek Belajar Analisis Data dengan Python')
st.text('Menggunakan data Brazilian E-Commerce Public Dataset')
st.logo('submission/gambar/Logo-its-biru-transparan.png', size="large")

st.header('Hasil Analisis Data')
"""
tab1, tab2, tab3 = st.tabs(['Tabs 1', 'Tabs 2', 'Tabs 3'])

with tab1:
    st.header('Total Order per Month')
    fig = plt.figure(figsize=(14, 8))

    sns.lineplot(data=total_order_per_months, x='month', y='total_orders',
             hue='year', palette=['#7E8AAD', '#45496A'], marker='o')
    plt.title('Jumlah Order per-Bulan Tahun 2017 dan 2018',
          fontsize=16, fontweight='bold', loc='center', pad=15)
    plt.xlabel('Bulan', fontsize=12)
    plt.ylabel('Jumlah Order', fontsize=12)
    plt.xticks(rotation=45)
    plt.legend(title='Tahun')
    plt.grid(True)
    st.pyplot(fig)

    with st.expander('Lihat Data'):
        st.write(total_order_per_months)
"""

with st.container(border=True):
    st.header('Total Order per Month')
    fig = plt.figure(figsize=(14, 8))

    sns.lineplot(data=total_order_per_months, x='month', y='total_orders',
             hue='year', palette=['#7E8AAD', '#45496A'], marker='o')
    plt.title('Jumlah Order per-Bulan Tahun 2017 dan 2018',
          fontsize=16, fontweight='bold', loc='center', pad=15)
    plt.xlabel('Bulan', fontsize=12)
    plt.ylabel('Jumlah Order', fontsize=12)
    plt.xticks(rotation=45)
    plt.legend(title='Tahun')
    plt.grid(True)
    st.pyplot(fig)

with st.sidebar:
    
    st.markdown('Perkenalkan, Saya Lazuardi Favian Fazari, mahasiswa Teknik Elektro ITS semester 7. Salam kenal.')
    st.markdown('LinkedIn: [Lazuardi Fazari](https://www.linkedin.com/in/lazuardi-fazari/)')
    st.markdown('Instagram: [@lazuardiii_ff](https://www.instagram.com/lazuardiii_ff/)')
    st.markdown('Website ini digunakan sebagai pemenuhan tugas akhir untuk course Belajar Data Analisis dengan Python di Dicoding.')
    st.markdown('Dataset yang digunakan adalah Brazilian E-Commerce Public Dataset yang dapat diakses melalui Kaggle. [Kaggle Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)')
    