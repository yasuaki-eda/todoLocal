
import streamlit as st
import pandas as pd
import altair as alt
import sqlite3
import os
import logging

# ログ設定
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'app.db')


# DB接続・初期化
try:
    conn = sqlite3.connect(DB_PATH)
    logging.info(f"DB接続成功: {DB_PATH}")
    # テーブル作成
    conn.execute('''CREATE TABLE IF NOT EXISTS todo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        done INTEGER DEFAULT 0
    )''')
    # 既存テーブルにcommentカラムがなければ追加
    try:
        conn.execute('ALTER TABLE todo ADD COLUMN comment TEXT')
    except Exception:
        pass
    conn.commit()
    logging.info("todoテーブル初期化完了（commentカラム追加）")
except Exception as e:
    logging.error(f"DB接続失敗: {e}")
    st.error(f"DB接続失敗: {e}")

st.title('TODO管理アプリ')
st.write('SQLite DB: ' + DB_PATH)



# ログ表示機能は削除


# TODO追加フォーム（コメント欄追加）
st.subheader('TODO追加')
with st.form(key='add_todo'):
    new_task = st.text_input('新しいTODOを入力')
    new_comment = st.text_area('コメント・メモ')
    submitted = st.form_submit_button('追加')
    if submitted and new_task:
        try:
            conn.execute('INSERT INTO todo (task, comment) VALUES (?, ?)', (new_task, new_comment))
            conn.commit()
            logging.info(f"TODO追加: {new_task}, コメント: {new_comment}")
            st.success('TODOを追加しました')
        except Exception as e:
            logging.error(f"TODO追加失敗: {e}")
            st.error(f"TODO追加失敗: {e}")


# TODO一覧表示・完了/削除機能
st.subheader('TODO一覧')
try:
    df_todo = pd.read_sql_query('SELECT id, task, comment, created_at, done FROM todo ORDER BY created_at DESC', conn)
    for idx, row in df_todo.iterrows():
        col1, col2, col3, col4, col5 = st.columns([4,3,2,2,2])
        with col1:
            st.write(f"{row['task']}")
        with col2:
            st.write(row['comment'] if row['comment'] else "")
        with col3:
            done = st.checkbox('完了', value=bool(row['done']), key=f"done_{row['id']}")
            if done != bool(row['done']):
                try:
                    conn.execute('UPDATE todo SET done=? WHERE id=?', (int(done), row['id']))
                    conn.commit()
                    logging.info(f"TODO完了状態変更: id={row['id']} -> {done}")
                    st.rerun()
                except Exception as e:
                    logging.error(f"完了状態変更失敗: {e}")
                    st.error(f"完了状態変更失敗: {e}")
        with col4:
            import datetime, pytz
            try:
                # SQLiteのcreated_atはUTCとして扱い、JSTに変換
                dt_utc = datetime.datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                dt_jst = dt_utc.replace(tzinfo=datetime.timezone.utc).astimezone(pytz.timezone('Asia/Tokyo'))
                st.write(dt_jst.strftime('%Y-%m-%d %H:%M:%S'))
            except Exception:
                st.write(row['created_at'])
        with col5:
            if st.button('削除', key=f"del_{row['id']}"):
                try:
                    conn.execute('DELETE FROM todo WHERE id=?', (row['id'],))
                    conn.commit()
                    logging.info(f"TODO削除: id={row['id']}")
                    st.rerun()
                except Exception as e:
                    logging.error(f"TODO削除失敗: {e}")
                    st.error(f"TODO削除失敗: {e}")
except Exception as e:
    logging.error(f"TODO一覧取得失敗: {e}")
    st.error(f"TODO一覧取得失敗: {e}")


# TODO件数・完了件数グラフ
st.subheader('日別TODO件数・完了件数グラフ')
try:
    df_count = pd.read_sql_query('''
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as todo_count,
            SUM(done) as done_count
        FROM todo
        GROUP BY DATE(created_at)
        ORDER BY date
    ''', conn)
    # データを棒グラフ用に変形
    df_melt = df_count.melt(id_vars=['date'], value_vars=['todo_count', 'done_count'],
                           var_name='type', value_name='count')
    type_map = {'todo_count': 'TODO件数', 'done_count': '完了件数'}
    df_melt['type'] = df_melt['type'].map(type_map)
    chart = alt.Chart(df_melt).mark_bar().encode(
        x=alt.X('date:T', title='日付'),
        y=alt.Y('count:Q', title='件数'),
        color=alt.Color('type:N', title='種別', scale=alt.Scale(domain=['TODO件数', '完了件数'], range=['skyblue', 'orange'])),
        column=alt.Column('type:N', title='種別', spacing=0)
    ).properties(width=40)
    # グループ化棒グラフ（横並び）
    chart = alt.Chart(df_melt).mark_bar().encode(
        x=alt.X('date:N', title='日付'),
        y=alt.Y('count:Q', title='件数'),
        color=alt.Color('type:N', title='種別', scale=alt.Scale(domain=['TODO件数', '完了件数'], range=['skyblue', 'orange'])),
        xOffset='type:N'
    ).properties(width=600)
    st.altair_chart(chart, use_container_width=True)
except Exception as e:
    st.write('グラフ表示エラー:', e)
