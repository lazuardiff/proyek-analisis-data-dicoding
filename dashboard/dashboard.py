import streamlit as st 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import datetime as dt
import matplotlib.image as mpimg
import urllib
from datetime import timedelta

# deklarasi fungsi-fungsi
def convert_to_datetime(data):
    columns_to_convert = ['order_purchase_timestamp', 'order_approved_at']
    for column in columns_to_convert:
        data[column] = pd.to_datetime(data[column])
    return data
    
def top_5_category_product(data):
    filtered_data = data.groupby('product_category_name_english')[
    'product_id'].count().reset_index()

    # mengurutkan data berdasarkan banyak data yang terjual
    filtered_data = filtered_data.sort_values(by='product_id', ascending=False)

    # mengubah nama kolom product_id menjadi total_product
    filtered_data.rename(columns={'product_id': 'total_product'}, inplace=True)
    return filtered_data

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

def review_score(data):
    filtered_data = data.groupby(
    'review_score')['order_id'].nunique().reset_index()
    filtered_data.rename(columns={'order_id': 'total_order'}, inplace=True)
    return filtered_data

def location_with_the_most_customers(data, customers_data):
    # Mengelompokkan data berdasarkan prefix kode pos dan menghitung jumlah state unik untuk setiap prefix
    other_state_geolocation = data.groupby(['geolocation_zip_code_prefix'])['geolocation_state'].nunique().reset_index(name='count')

    other_state_geolocation[other_state_geolocation['count']>= 2].shape

    # Mengelompokkan data berdasarkan prefix kode pos dan state, menghitung jumlahnya, dan menghapus duplikasi berdasarkan prefix kode pos
    max_state = data.groupby(['geolocation_zip_code_prefix','geolocation_state']).size().reset_index(name='count').drop_duplicates(subset = 'geolocation_zip_code_prefix').drop('count',axis=1)

    geolocation_silver = data.groupby(['geolocation_zip_code_prefix','geolocation_city','geolocation_state'])[['geolocation_lat','geolocation_lng']].median().reset_index()
    geolocation_silver = geolocation_silver.merge(max_state,on=['geolocation_zip_code_prefix','geolocation_state'],how='inner')

    customers_silver = customers_data.merge(geolocation_silver,left_on='customer_zip_code_prefix',right_on='geolocation_zip_code_prefix',how='inner')
    customers_silver.drop_duplicates(subset='customer_unique_id')

    return customers_silver

def average_rating_by_delivery_status(data):
    rating_by_delivery = data.groupby('delivered_on_time')['review_score'].mean().reset_index()
    rating_by_delivery['delivered_on_time'] = rating_by_delivery['delivered_on_time'].map({True: 'On Time', False: 'Late'})
    
    return rating_by_delivery

def RFM_analysis(data):
    # Mengelompokkan data berdasarkan customer_unique_id dan menghitung nilai recency, frequency, dan monetary untuk setiap pelanggan
    rfm_data = data.groupby(by='customer_unique_id', as_index=False).agg({
    'order_purchase_timestamp': 'max',
    'order_id': 'nunique',
    'payment_value': 'sum'
})

# mengubah nama kolom
    rfm_data.columns = ['customer_unique_id',
                        'max_order_timestamp', 'frequency', 'monetary']

    # menghitung recency
    rfm_data['max_order_timestamp'] = rfm_data['max_order_timestamp'].dt.date
    recent_date = data['order_purchase_timestamp'].dt.date.max()

    def calculate_recency(order_date):
        return (recent_date - order_date).days

    rfm_data['recency'] = rfm_data['max_order_timestamp'].apply(calculate_recency)
    rfm_data.drop('max_order_timestamp', axis=1, inplace=True)
    rfm_data.head()

        # menghitung recency
    recent_date = data['order_purchase_timestamp'].max() + timedelta(days=1)

    # mengelompokkan data berdasarkan customer_unique_id dan menghitung nilai recency, frequency, dan monetary untuk setiap pelanggan
    rfm_data = data.groupby(by='customer_unique_id').agg({
        'order_purchase_timestamp': lambda x: (recent_date - x.max()).days,
        'order_id': 'nunique',
        'payment_value': 'sum'
    }).reset_index()

    # mengubah nama kolom
    rfm_data.rename(columns={
        'order_purchase_timestamp': 'recency',
        'order_id': 'frequency',
        'payment_value': 'monetary'
    }, inplace=True)

    # memberikan skor R, F, dan M dari 1 hingga 5 berdasarkan kuantiles
    rfm_data['R_Score'] = pd.qcut(rfm_data['recency'], 5, labels=[
                                  5, 4, 3, 2, 1]).astype(int)
    rfm_data['F_Score'] = pd.qcut(rfm_data['frequency'].rank(
        method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm_data['M_Score'] = pd.qcut(rfm_data['monetary'], 5, labels=[
                                  1, 2, 3, 4, 5]).astype(int)

    rfm_data['RFM_Score'] = rfm_data['R_Score'].map(
        str) + rfm_data['F_Score'].map(str) + rfm_data['M_Score'].map(str)

    # fungsi segmentasi customer berdasarkan RFM Score
    def segment(x):
        if x['R_Score'] >= 4 and x['F_Score'] >= 4 and x['M_Score'] >= 4:
            return 'Best Customers'
        elif x['R_Score'] >= 4 and x['F_Score'] <= 2:
            return 'New Customers'
        elif x['R_Score'] >= 3 and x['F_Score'] >= 3 and x['M_Score'] >= 3:
            return 'Loyal Customers'
        else:
            return 'Others'

    rfm_data['Segment'] = rfm_data.apply(segment, axis=1)

    return rfm_data

# inisialisasi tampilan awal
st.set_page_config(
    page_title="Proyek Dicoding",
    page_icon="gambar/lambang-its-png-v1.png",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'about': 'Website ini digunakan sebagai pemenuhan tugas akhir untuk course Belajar Data Analisis dengan Python di Dicoding.'
    }
)

# load data
all_df = pd.read_csv('dashboard/merge_all.csv')
customer_data=pd.read_csv("data/customers_dataset.csv")
geolocation_data = pd.read_csv("data/geolocation_dataset.csv")
all_df = convert_to_datetime(all_df)

# assign data to variable
total_order_per_months = total_order_per_month(all_df)
top_5_category_products = top_5_category_product(all_df)
order_by_review_score = review_score(all_df)
customer_location = location_with_the_most_customers(geolocation_data, customer_data)
rating_by_delivery = average_rating_by_delivery_status(all_df)
rfm_data = RFM_analysis(all_df)

st.title('Proyek Belajar Analisis Data dengan Python')
st.text('Menggunakan data Brazilian E-Commerce Public Dataset')
st.logo('gambar/Logo-its-biru-transparan.png', size="large")


with st.sidebar:
    st.markdown('Perkenalkan, Saya Lazuardi Favian Fazari, mahasiswa Teknik Elektro ITS semester 7. Salam kenal.')
    st.markdown('LinkedIn: [Lazuardi Fazari](https://www.linkedin.com/in/lazuardi-fazari/)')
    st.markdown('Instagram: [@lazuardiii_ff](https://www.instagram.com/lazuardiii_ff/)')
    #st.markdown('Website ini digunakan sebagai pemenuhan tugas akhir untuk course Belajar Data Analisis dengan Python di Dicoding.')
    st.markdown('Dataset yang digunakan adalah Brazilian E-Commerce Public Dataset yang dapat diakses melalui Kaggle. [Kaggle Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)')

st.markdown(
    '<h2 style="text-align: center; color: #FFFFFF;">Data Visualization untuk menjawab pertanyaan bisnis</h2>',
    unsafe_allow_html=True
)
st.markdown('Pertanyaan bisnis yang saya ajukan adalah:  \n1. Kategori produk apa yang paling banyak dan paling sedikit terjual?  \n2. Bagaimana tren penjualan berdasarkan waktu?  \n3. Bagaimana skor review mempengaruhi penjualan?  \n4. Dimanakah lokasi yang memiliki pelanggan terbanyak?  \n5. Apakah pengiriman tepat waktu dapat mempengaruhi review score produk?')

# inisialisasi tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7=st.tabs(['Pertanyaan 1', 'Pertanyaan 2', 'Pertanyaan 3', 'Pertanyaan 4', 'Pertanyaan 5', 'RFM Analysis', 'Kesimpulan'])

with tab1:
    # visualisasi data pertanyaan 1
    with st.container():
        st.markdown(
            '<h3 style="text-align: center; color: #FFFFFF;">Top 5 Kategori Produk Paling Banyak dan Paling Sedikit Terjual</h3>',
            unsafe_allow_html=True
        )
        st.markdown('1. Kategori produk apa yang paling banyak dan paling sedikit terjual?')
        
        fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(20, 6))
        colors = ['#254E7A', '#CBE3EF', '#CBE3EF', '#CBE3EF', '#CBE3EF']
    
        sns.barplot(x='total_product', y='product_category_name_english', data=top_5_category_products.head(
            5), hue='product_category_name_english', palette=colors, ax=ax[0])
        ax[0].set_title('Top 5 Kategori Produk Paling Banyak Terjual',
                        loc='center', fontsize=16, fontweight='bold')
        ax[0].set_xlabel('Total Produk', fontsize=12)
        ax[0].set_ylabel('Kategori Produk', fontsize=12)
        ax[0].tick_params(axis='y', labelsize=12)
        ax[0].tick_params(axis='x', labelsize=12)
    
        sns.barplot(x='total_product', y='product_category_name_english', data=top_5_category_products.sort_values(
            by='total_product', ascending=True).head(5), hue='product_category_name_english', palette=colors, ax=ax[1])
        ax[1].set_title('Top 5 Kategori Produk Paling Sedikit Terjual',
                        loc='center', fontsize=16, fontweight='bold')
        ax[1].set_xlabel('Total Produk', fontsize=12)
        ax[1].set_ylabel('Kategori Produk', fontsize=12)
        ax[1].invert_xaxis()
        ax[1].yaxis.set_label_position("right")
        ax[1].yaxis.tick_right()
        ax[1].tick_params(axis='y', labelsize=12)
        ax[1].tick_params(axis='x', labelsize=12)
    
        plt.tight_layout()
        st.pyplot(fig)
    
        with st.expander('Hasil Analisis Data'):
            st.write('pada gambar di atas, dapat diketahui bahwa kategori produk yang paling banyak terjual adalah "bed_bath_table" dengan penjualan sekitar 12000 dan yang paling sedikit terjual adalah "security_and_services" dengan penjualan sekitar < 5 ')
            st.write('Data yang digunakan adalah:', top_5_category_products)

with tab2:
    # visualisasi data pertanyaan 2
    with st.container():
        st.markdown(
            '<h3 style="text-align: center; color: #FFFFFF;">Jumlah Order per-Bulan</h3>',
            unsafe_allow_html=True
        )
        st.markdown('2. Bagaimana tren penjualan berdasarkan waktu?')

        fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(14, 10))
        sns.lineplot(data=total_order_per_months[total_order_per_months['year'] == 2017], x='month', y='total_orders', marker='o', ax=ax[0], color='#254E7A')
        ax[0].set_title('Jumlah Order per-Bulan Tahun 2017', loc='center', fontsize=16, fontweight='bold')
        ax[0].set_xlabel('Bulan', fontsize=12)
        ax[0].set_ylabel('Jumlah Order', fontsize=12)
        ax[0].tick_params(axis='y', labelsize=12)
        ax[0].tick_params(axis='x', labelsize=12)
        ax[0].grid(True)

        sns.lineplot(data=total_order_per_months[total_order_per_months['year'] == 2018], x='month', y='total_orders', marker='o', ax=ax[1], color='#254E7A')
        ax[1].set_title('Jumlah Order per-Bulan Tahun 2018', loc='center', fontsize=16, fontweight='bold')
        ax[1].set_xlabel('Bulan', fontsize=12)
        ax[1].set_ylabel('Jumlah Order', fontsize=12)
        ax[1].tick_params(axis='y', labelsize=12)
        ax[1].tick_params(axis='x', labelsize=12)
        ax[1].grid(True)

        plt.tight_layout()
        st.pyplot(fig)

        with st.expander('Hasil Analisis Data'):
            st.write('dari data yang telah divisualisasikan, jumlah order pada tahun 2017 meningkat pesat dari Januari 2017 hingga Desember 2017. sayangnya, pada Desember 2017 hingga Oktober 2018, jumlah order terus mengalami penurunan yang signifikan.')
            st.write('Data yang digunakan adalah:', total_order_per_months)

with tab3:
    with st.container():
        st.markdown(
            '<h3 style="text-align: center; color: #FFFFFF;">Jumlah Order berdasarkan Skor Review</h3>',
            unsafe_allow_html=True
        )
        st.markdown('3. Bagaimana skor review mempengaruhi penjualan?')

        fig = plt.figure(figsize=(14, 8))
        sns.barplot(data=order_by_review_score, x='review_score',
                    y='total_order', palette='viridis')
        plt.title('Order berdasarkan Skor Review', fontsize=16, fontweight='bold')
        plt.xlabel('Score Review', fontsize=12)
        plt.ylabel('Jumlah Order', fontsize=12)
        plt.grid(axis='y', linestyle='--')

        st.pyplot(fig)

        with st.expander('Hasil Analisis Data'):
            st.write('berdasarkan data yang sudah divisualisasikan, mayoritas order memiliki skor review tinggi, dengan skor 5.0 mendominasi lebih dari 50.000 order, menunjukkan tingkat kepuasan pelanggan yang sangat tinggi.')
            st.write('Data yang digunakan adalah:', order_by_review_score)
    
with tab4:
    with st.container():
        st.markdown(
            '<h3 style="text-align: center; color: #FFFFFF;">Lokasi dengan Pelanggan Terbanyak</h3>',
            unsafe_allow_html=True
        )
        st.markdown('4. Dimanakah lokasi yang memiliki pelanggan terbanyak?')

        brazil = mpimg.imread(urllib.request.urlopen('https://i.pinimg.com/originals/3a/0c/e1/3a0ce18b3c842748c255bc0aa445ad41.jpg'),'jpg')
        fig, ax=plt.subplots(figsize=(10,10))
        ax.scatter(customer_location['geolocation_lng'], customer_location['geolocation_lat'], alpha=0.3, s=0.3, c='maroon')
        plt.axis('off')
        plt.imshow(brazil, extent=[-73.98283055, -33.8,-33.75116944,5.4])
        #for _, row in customer_location.iterrows():
        #    ax.text(row['geolocation_lng'], row['geolocation_lat'], row['geolocation_city'], fontsize=6, color='black', alpha=0.6)
        st.pyplot(fig)

        with st.expander('Hasil Analisis Data'):
            st.write('berdasarkan data yang sudah divisualisasikan, pelanggan terbanyak berada di wilayah tenggara Brazil, dengan kota Sao Paulo sebagai kota dengan pelanggan terbanyak.')
            st.write('Data yang digunakan adalah:', customer_location)

with tab5:
    with st.container():
        st.markdown(
            '<h3 style="text-align: center; color: #FFFFFF;">Rata-rata Rating Berdasarkan Status Pengiriman</h3>',
            unsafe_allow_html=True
        )
        st.markdown('5. Apakah pengiriman tepat waktu dapat mempengaruhi review score produk?')

        fig=plt.figure(figsize=(12, 6))
        sns.barplot(data=rating_by_delivery, x='delivered_on_time', y='review_score', palette='viridis')
        plt.title('Rata-rata Rating Berdasarkan Status Pengiriman', fontsize=16, fontweight='bold')
        plt.xlabel('Status Pengiriman', fontsize=12)
        plt.ylabel('Rata-rata Rating', fontsize=12)
        plt.ylim(0, 5)
        plt.grid(axis='y', linestyle='--')
        plt.tight_layout()
        
        st.pyplot(fig)

        with st.expander('Hasil Analisis Data'):
            st.write('berdasarkan data yang sudah divisualisasikan, pengiriman tepat waktu memiliki rata-rata rating yang lebih tinggi dibandingkan pengiriman yang terlambat.')
            st.write('Data yang digunakan adalah:', rating_by_delivery)

with tab6:
    st.markdown(
        '<h3 style="text-align: center; color: #FFFFFF;">RFM Analysis</h3>',
        unsafe_allow_html=True
    )
    st.markdown('RFM Analysis adalah metode analisis yang digunakan untuk mengelompokkan pelanggan berdasarkan tiga faktor: Recency, Frequency, dan Monetary. Recency adalah jarak waktu antara transaksi terakhir pelanggan dengan waktu saat ini, Frequency adalah jumlah transaksi yang dilakukan oleh pelanggan, dan Monetary adalah total uang yang dihabiskan oleh pelanggan. Dengan metode ini, kita dapat mengetahui pelanggan mana yang paling berharga dan pelanggan mana yang perlu ditingkatkan.')

    col1, col2, col3 = st.columns(3, vertical_alignment='center', gap='small')
    with col1:
        st.markdown('<h4 style="text-align: center; color: #FFFFFF; font-size:20px;">Recency</h4>', unsafe_allow_html=True)
        fig=plt.figure(figsize=(10, 6))
        sns.histplot(rfm_data['recency'], bins=30, kde=False, color='blue')
        plt.title('Distribusi Recency')
        plt.xlabel('Recency (hari)')
        plt.ylabel('Jumlah Pelanggan')
        st.pyplot(fig)

    with col2:
        st.markdown('<h4 style="text-align: center; color: #FFFFFF; font-size:20px;">Frequency</h4>', unsafe_allow_html=True)
        fig=plt.figure(figsize=(10, 6))
        sns.histplot(rfm_data['frequency'], bins=30, kde=False, color='green')
        plt.title('Distribusi Frequency')
        plt.xlabel('Frequency (transaksi)')
        plt.ylabel('Jumlah Pelanggan')
        st.pyplot(fig)

    with col3:
        st.markdown('<h4 style="text-align: center; color: #FFFFFF; font-size:20px;">Monetary</h4>', unsafe_allow_html=True)
        fig=plt.figure(figsize=(10, 6))
        sns.histplot(rfm_data['monetary'], bins=30, kde=False, color='red')
        plt.title('Distribusi Monetary')
        plt.xlabel('Monetary (total pembelian)')
        plt.ylabel('Jumlah Pelanggan')
        st.pyplot(fig)
    
    segment_counts = rfm_data['Segment'].value_counts()

    fig=plt.figure(figsize=(8, 8))
    plt.pie(segment_counts.values, labels=segment_counts.index,
            autopct='%1.1f%%', startangle=140)
    plt.title('Distribusi Segmen Customer')
    plt.axis('equal')
    st.pyplot(fig)

    with st.expander('Hasil Analisis Data'):
        st.write("""
                **Kesimpulan RFM Analysis:**

                - **Recency**: Mayoritas customer melakukan pembelian terakhir antara 100-400 hari lalu.
                - **Frequency**: Sebagian besar customer hanya melakukan 1-2 transaksi.
                - **Monetary**: Nilai pembelian rata-rata pelanggan cenderung rendah.
                - **Segmentasi Customer**:
                    - **Best Customer**: Customer yang perlu dipertahankan.
                    - **New Customer**: Customer baru dengan recency tinggi tetapi frekuensi rendah.
                    - **Loyal Customer**: Customer yang sering bertransaksi.
                    - **Others**: Customer dengan skor RFM rendah.
                """)
        st.write('Data yang digunakan adalah:', rfm_data)

with tab7:
    st.markdown(
        '<h3 style="text-align: center; color: #FFFFFF;">Kesimpulan</h3>',
        unsafe_allow_html=True
    )
    st.markdown('Dari hasil analisis data yang telah dilakukan, dapat disimpulkan bahwa:')
    st.markdown('1. Kategori produk yang paling banyak terjual adalah "bed_bath_table" dengan penjualan sekitar 12000 dan yang paling sedikit terjual adalah "security_and_services" dengan penjualan sekitar < 5.')
    st.markdown('2. Jumlah order pada tahun 2017 meningkat pesat dari Januari 2017 hingga Desember 2017. sayangnya, pada Desember 2017 hingga Oktober 2018, jumlah order terus mengalami penurunan yang signifikan.')
    st.markdown('3. Mayoritas order memiliki skor review tinggi, dengan skor 5.0 mendominasi lebih dari 50.000 order, menunjukkan tingkat kepuasan pelanggan yang sangat tinggi.')
    st.markdown('4. Pelanggan terbanyak berada di wilayah tenggara Brazil, dengan kota Sao Paulo sebagai kota dengan pelanggan terbanyak.')
    st.markdown('5. Pengiriman tepat waktu memiliki rata-rata rating yang lebih tinggi dibandingkan pengiriman yang terlambat.')
    st.markdown('6. Berdasarkan RFM Analysis, mayoritas customer melakukan pembelian terakhir antara 100-400 hari lalu, sebagian besar customer hanya melakukan 1-2 transaksi, dan nilai pembelian rata-rata pelanggan cenderung rendah.')
    st.markdown('7. Segmentasi customer terdiri dari Best Customer, New Customer, Loyal Customer, dan Others.')