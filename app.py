from textwrap import shorten
from altair.vegalite.v4.schema.core import DataFormat
from utils.utils import *

from dotenv import load_dotenv

load_dotenv()

PASSWORD = os.environ.get('PASSWORD')

st.set_page_config(page_title="Quake-Typhoon Explorer", page_icon="./assets/icon.png")

# remove 'Made with Streamlit' footer MainMenu {visibility: hidden;}
hide_streamlit_style = """
			<style>
			footer {visibility: hidden;}
			</style>
			"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# modify the margins
st.markdown(
    f"""
    <style>
        .reportview-container .main .block-container{{
            max-width: 900px;
            padding-left: 3rem;
            padding-right: 3rem;
            padding-top: 1rem;
            padding-bottom: 1rem;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

make_map_responsive = """
    <style>
    [title~="st.iframe"] { width: 100%}
    </style>

    <style>
    [data-testid="stMetricDelta"] svg {
        display: none;
    }
    </style>
    """
st.markdown(make_map_responsive, unsafe_allow_html=True)

st.markdown(
    "<style>div.row-widget.stRadio > div{flex-direction:row;}</style>",
    unsafe_allow_html=True,
)

st.sidebar.subheader("Quake-Typhoon Explorer")
app = st.sidebar.selectbox(
    label="Select app", options=["Earthquake Explorer", "Typhoon Explorer",]
)
nav = st.sidebar.radio(
    label="Navigation",
    options=[
        "About QT Explorer",
        "Dashboard Proper",
        "Additional Analysis",
        "Tabular Datasource",
        "Discussion Board",
    ],
)

# user_upload = st.sidebar.file_uploader(label="Upload file", type=['csv'], key='typhoon')


def main():
    if app == "Typhoon Explorer":
        if nav in ["Dashboard Proper", "Additional Analysis", "Tabular Datasource"]:
            st.title("Typhoon Track Explorer")
        st.markdown("---")
        # with st.spinner(text="Loading resources..."):
        df = read_data()
        points = read_points()

        path = read_path()
        admin = gpd.read_feather("./assets/PHL_adm1.feather")
        par = gpd.read_feather("./assets/par.feather")
        points_par = gpd.read_feather("./assets/typhoon_path_points.feather")

        temp_df = df.sort_values("WMO_WIND", ascending=True).drop_duplicates(
            ["SID", "NAME"], keep="last"
        )[["SID", "NAME", "WMO_WIND", "TRACK_TYPE", "Year", "Month"]]

        if nav in ["Dashboard Proper", "Tabular Datasource"]:
            with st.form(key="form1", clear_on_submit=False):
                if nav == "Dashboard Proper":
                    filter_type = st.radio(
                        "Filter Method",
                        options=["Spatial-Temporal", "Typhoon Name", "Top List"],
                    )
                else:
                    filter_type = st.radio(
                        "Filter Method", options=["Spatial-Temporal", "Typhoon Name"]
                    )

                f1, f2, f3 = st.columns((1.5, 3, 3))

                if filter_type == "Spatial-Temporal":
                    with f1:
                        temporal_filter = st.selectbox(
                            label="Temporal Filter",
                            options=["None", "By Year", "By Month", "By Date"],
                            help="Filter data by year or month. Default is None.",
                        )
                    if nav == "Tabular Datasource":
                        with f2:
                            spatial_filter = st.multiselect(
                                label="Spatial Filter",
                                options=[],
                                help="This option is unavailable under Tabular Datasource Tab",
                            )
                    else:
                        with f2:
                            spatial_filter = st.multiselect(
                                label="Spatial Filter",
                                options=admin["NAME_1"].unique(),
                                help="Filter data by provincial boundary. Default is None",
                            )
                    with f3:
                        typhoon_filter = st.multiselect(
                            label="Typhoon Name (Int'l) Filter",
                            options=[],
                            help="This option is unavailable under Spatial-Temporal Filter",
                        )

                    if temporal_filter == "None":
                        pass

                    elif temporal_filter == "By Year":
                        year_list = df["Year"].unique()
                        start_year, end_year = st.select_slider(
                            label="Select Year",
                            options=year_list,
                            value=[2019, 2021],
                            help="Use the slider to select start and end year.",
                        )
                    elif temporal_filter == "By Month":
                        start_month, end_month = st.select_slider(
                            label="Select Month",
                            options=month_list,
                            value=["Aug", "Sep"],
                            help="Use the slider to select start and end month.",
                        )
                    elif temporal_filter == "By Date":
                        date_options = points["Date"].dt.date.unique()
                        start_date, end_date = st.select_slider(
                            label="Select Date",
                            options=date_options,
                            value=(date_options[0], date_options[-1]),
                            help="Use the slider to select start and end date.",
                        )

                if filter_type == "Typhoon Name":
                    with f1:
                        temporal_filter = st.selectbox(
                            label="Temporal Filter",
                            options=[],
                            help="This option is unavailable under Typhoon Name Filter.",
                        )
                    with f2:
                        spatial_filter = st.multiselect(
                            label="Spatial Filter",
                            options=[],
                            help="This option is unavailable under Typhoon Name Filter.",
                        )
                    with f3:
                        typhoon_filter_option = np.sort(df["NAME"].unique())
                        typhoon_filter = st.multiselect(
                            label="Typhoon Name (Int'l) Filter",
                            options=typhoon_filter_option,
                            help="Filter data by Typhoon Name",
                        )

                if filter_type == "Top List":
                    with f1:
                        temporal_filter = st.selectbox(
                            label="Temporal Filter",
                            options=[],
                            help="This option is unavailable under Top List Filter.",
                        )
                    with f2:
                        spatial_filter = st.multiselect(
                            label="Spatial Filter",
                            options=[],
                            help="This option is unavailable under Top List Filter.",
                        )
                    with f3:
                        typhoon_filter = st.multiselect(
                            label="Typhoon Name (Int'l) Filter",
                            options=[],
                            help="This option is unavailable under Top List Filter.",
                        )

                submit_button = st.form_submit_button(label="Run Filter")

            if filter_type == "Spatial-Temporal":
                if temporal_filter == "None":
                    sid = df["SID"].unique()

                elif temporal_filter == "By Year":
                    sid = df[df["Year"].isin(range(start_year, end_year + 1))][
                        "SID"
                    ].unique()
                    points = points[
                        points["Year"].isin(range(start_year, end_year + 1))
                    ]

                elif temporal_filter == "By Month":
                    sid = df[
                        df["Month"].isin(
                            range(
                                mapping_dict[start_month], mapping_dict[end_month] + 1
                            )
                        )
                    ]["SID"].unique()
                    points = points[
                        points["Month"].isin(
                            range(
                                mapping_dict[start_month], mapping_dict[end_month] + 1
                            )
                        )
                    ]

                elif temporal_filter == "By Date":
                    sid = df[
                        (
                            (df["Date"].dt.date >= start_date)
                            & (df["Date"].dt.date <= end_date)
                        )
                    ]["SID"].unique()
                    points = points[
                        (points["Date"].dt.date >= start_date)
                        & (points["Date"].dt.date <= end_date)
                    ]

            if filter_type == "Typhoon Name":
                if len(typhoon_filter) == 0:
                    sid = df["SID"].unique()
                else:
                    sid = df[df["NAME"].isin(typhoon_filter)]["SID"].unique()

            if filter_type == "Top List":
                gl_map = KeplerGl()
                config = read_config("./assets/config2.txt")
                gl_map.add_data(data=par, name="PAR")
                gl_map.config = config
                topn_list = st.selectbox(
                    label="Top List Filter",
                    options=["Deadliest", "Wettest", "Costliest", "All"],
                    help="You can select from four (4) lists: Deadliest, Wettest, Costliest, All. Default is Deadliest.",
                )
                deadliest = gpd.read_feather("./assets/deadliest.feather")
                wettest = gpd.read_feather("./assets/wettest.feather")
                wettest.columns = [
                    "SID",
                    "NAME",
                    "LOCAL",
                    "YEAR",
                    "PRECIPITATION (MM)",
                    "geometry",
                ]
                costliest = gpd.read_feather("./assets/costliest.feather")
                costliest.columns = [
                    "SID",
                    "NAME",
                    "LOCAL",
                    "YEAR",
                    "DAMAGE (BILLION PHP)",
                    "geometry",
                ]

                deadliest_points = points_par[
                    points_par["SID"].isin(deadliest["SID"].unique())
                ]
                wettest_points = points_par[
                    points_par["SID"].isin(wettest["SID"].unique())
                ]
                costliest_points = points_par[
                    points_par["SID"].isin(costliest["SID"].unique())
                ]

                if topn_list == "Deadliest":
                    gl_map.add_data(data=deadliest, name="Deadliest Typhoons Track")
                    gl_map.add_data(
                        data=deadliest_points, name="Deadliest Typhoons Points"
                    )
                    keplergl_static(gl_map)
                    dl_button = st.empty()
                    deadliest = deadliest.drop(["geometry"], axis=1)
                    st.subheader("Deadliest Typhoons between 1980 - present")
                    st.table(deadliest)
                elif topn_list == "Wettest":
                    gl_map.add_data(data=wettest, name="Wettest Typhoons Track")
                    gl_map.add_data(data=wettest_points, name="Wettest Typhoons Points")
                    keplergl_static(gl_map)
                    dl_button = st.empty()
                    wettest = wettest.drop(["geometry"], axis=1)
                    st.subheader("Wettest Typhoons between 1980 - present")
                    st.table(wettest)
                elif topn_list == "Costliest":
                    gl_map.add_data(data=costliest, name="Costliest Typhoons Track")
                    gl_map.add_data(
                        data=costliest_points, name="Costliest Typhoons Points"
                    )
                    costliest = costliest.drop(["geometry"], axis=1)
                    keplergl_static(gl_map)
                    dl_button = st.empty()
                    st.subheader("Costliest Typhoons between 1980 - present")
                    st.table(costliest)
                else:
                    gl_map.add_data(data=deadliest, name="Deadliest Typhoons Track")
                    gl_map.add_data(
                        data=deadliest_points, name="Deadliest Typhoons Points"
                    )
                    gl_map.add_data(data=wettest, name="Wettest Typhoons Track")
                    gl_map.add_data(data=wettest_points, name="Wettest Typhoons Points")
                    gl_map.add_data(data=costliest, name="Costliest Typhoons Track")
                    gl_map.add_data(
                        data=costliest_points, name="Costliest Typhoons Points"
                    )
                    keplergl_static(gl_map)
                    dl_button = st.empty()

                gl_map.save_to_html()
                download_file = codecs.open('keplergl_map.html', 'r', 'utf-8').read()

                with dl_button:
                    st.download_button(label='Download interactive map', data=download_file,                 
                            file_name="typhoon-tracks.html",
                            mime="text/html")
                return

        if nav == "Dashboard Proper":
            m1, m2, m3, m4 = st.columns(4)
            count = m1.empty()
            landfall = m2.empty()
            strongest_typhoon = m3.empty()
            max_wind = m4.empty()

            path = path.merge(temp_df, on=["SID", "NAME"], how="left")
            path_filtered = path[path["SID"].isin(sid)]
            path_filtered = path_filtered.drop(["OBJECTID", "Shape_Leng"], axis=1)
            path_filtered["intersect"] = 0.0

            if len(spatial_filter) > 0:
                for i in path_filtered.index:
                    for j in admin[admin["NAME_1"].isin(spatial_filter)].index:
                        if path_filtered.loc[i, "geometry"].intersects(
                            admin.loc[j, "geometry"]
                        ):
                            path_filtered.loc[i, "intersect"] = 1.0
                            break
                path_filtered = path_filtered[path_filtered["intersect"] > 0]

            ct = path_filtered.shape[0]
            if ct == 0:
                st.error("No data selected for the indicated filter/s. Please refresh.")
                return
            with count:
                st.metric(label="Typhoon Count", value=ct)

            lf = int(path_filtered["Land Fall"].value_counts().squeeze())
            with landfall:
                st.metric(
                    label="Land Fall Count",
                    value=lf,
                    delta=f"{lf/ct:.2%}",
                    delta_color="off",
                )

            strong_ty = path_filtered.iloc[path_filtered["WMO_WIND"].argmax(), 1]
            strong_year = path_filtered.iloc[path_filtered["WMO_WIND"].argmax(), -3]
            strong_month = path_filtered.iloc[path_filtered["WMO_WIND"].argmax(), -2]

            strongest_typhoon.metric(
                label="Strongest Typhoon",
                value=strong_ty,
                delta=f"{month_list[int(strong_month)-1]} {int(strong_year)}",
                delta_color="off",
            )

            max_path = gpd.GeoDataFrame(
                path_filtered.iloc[path_filtered["WMO_WIND"].argmax()]
            ).T
            wind = int(path_filtered["WMO_WIND"].max().squeeze()) * 1.852
            max_wind.metric(label="Max Wind (KPH)", value=millify(wind))

            points_par = points_par[
                points_par["SID"].isin(path_filtered["SID"].unique())
            ]
            points_par["WMO_WIND"] = points_par["WMO_WIND"] * 1.852

            if len(typhoon_filter) == 0:
                config = read_config("./assets/config.txt")
            else:
                config = read_config("./assets/config1.txt")

            gl_map = KeplerGl()
            gl_map.config = config
            gl_map.add_data(data=path_filtered, name="Typhoon Tracks")
            gl_map.add_data(data=max_path, name="Strongest typhoon")
            gl_map.add_data(data=points_par, name="Typhoon Track Points")
            gl_map.add_data(data=par, name="PAR")
            keplergl_static(gl_map)

            gl_map.save_to_html()

            download_file = codecs.open('keplergl_map.html', 'r', 'utf-8').read()

            st.download_button(label='Download interactive map', data=download_file,                 
                        file_name="typhoon-tracks.html",
                        mime="text/html")

            with st.expander("Click to hide/view visualization", expanded=True):
                typhoon_per_year = (
                    path_filtered.groupby("Year")
                    .agg({"SID": "count", "Land Fall": "sum"})
                    .sort_index()
                )
                typhoon_per_year = typhoon_per_year.reset_index()

                moving_average = (
                    typhoon_per_year[["SID", "Land Fall"]].rolling(window=5).mean()
                )
                moving_average.columns = ["rolling_SID", "rolling_Land Fall"]

                typhoon_per_year = typhoon_per_year.merge(
                    moving_average, left_index=True, right_index=True
                )

                nearest1 = alt.selection(
                    type="single",
                    nearest=True,
                    on="mouseover",
                    fields=["Year"],
                    empty="none",
                )

                selectors1 = (
                    alt.Chart(typhoon_per_year)
                    .mark_point()
                    .encode(x="Year:O", opacity=alt.value(0))
                    .add_selection(nearest1)
                )

                rules = (
                    alt.Chart(typhoon_per_year)
                    .mark_rule(color="gray")
                    .encode(x="Year:O",)
                    .transform_filter(nearest1)
                )

                c1 = (
                    alt.Chart(typhoon_per_year)
                    .mark_area(
                        interpolate="cardinal",
                        line={"color": "#444936"},
                        color=alt.Gradient(
                            gradient="linear",
                            stops=[
                                alt.GradientStop(color="#ADB0B5", offset=0),
                                alt.GradientStop(color="#D9D9C2", offset=1),
                            ],
                            x1=1,
                            x2=1,
                            y1=1,
                            y2=0,
                        ),
                    )
                    .encode(
                        x=alt.X("Year:O"),
                        y=alt.Y("SID:Q", title="Count"),
                        tooltip=[
                            alt.Tooltip("Year:O", title="Year"),
                            alt.Tooltip("SID:Q", title="Typhoon Occurence"),
                        ],
                    )
                )

                # Draw points on the line, and highlight based on selection
                point1 = c1.mark_point(color="#A3AF80").encode(
                    opacity=alt.condition(nearest1, alt.value(1), alt.value(0))
                )

                # Draw text labels near the points, and highlight based on selection
                text1 = c1.mark_text(align="left", dx=5, dy=-5).encode(
                    text=alt.condition(nearest1, "SID:Q", alt.value(" "))
                )

                c2 = (
                    alt.Chart(typhoon_per_year)
                    .mark_area(
                        interpolate="cardinal",
                        line={"color": "#1D3D65"},
                        color=alt.Gradient(
                            gradient="linear",
                            stops=[
                                alt.GradientStop(color="#ADB0B5", offset=0),
                                alt.GradientStop(color="#8BB2BE", offset=1),
                            ],
                            x1=1,
                            x2=1,
                            y1=1,
                            y2=0,
                        ),
                    )
                    .encode(
                        x=alt.X("Year:O"),
                        y=alt.Y("Land Fall:Q", title="Count"),
                        tooltip=[
                            alt.Tooltip("Year:O", title="Year"),
                            alt.Tooltip("Land Fall:Q", title="Land Fall"),
                        ],
                    )
                )

                # Draw points on the line, and highlight based on selection
                point2 = c2.mark_point().encode(
                    opacity=alt.condition(nearest1, alt.value(1), alt.value(0))
                )

                # Draw text labels near the points, and highlight based on selection
                text2 = c2.mark_text(align="left", dx=5, dy=-5).encode(
                    text=alt.condition(nearest1, "Land Fall:Q", alt.value(" "))
                )

                m1 = (
                    alt.Chart(typhoon_per_year.dropna(axis=0))
                    .mark_area(
                        interpolate="cardinal",
                        line={"color": "#444936"},
                        color=alt.Gradient(
                            gradient="linear",
                            stops=[
                                alt.GradientStop(color="#ADB0B5", offset=0),
                                alt.GradientStop(color="#D9D9C2", offset=1),
                            ],
                            x1=1,
                            x2=1,
                            y1=1,
                            y2=0,
                        ),
                    )
                    .encode(
                        x=alt.X("Year:O"),
                        y=alt.Y("rolling_SID:Q", title="Count"),
                        tooltip=[
                            alt.Tooltip("Year:O", title="Year"),
                            alt.Tooltip("rolling_SID:Q", title="Typhoon Occurence"),
                        ],
                    )
                )
                # Draw points on the line, and highlight based on selection
                point3 = m1.mark_point().encode(
                    opacity=alt.condition(nearest1, alt.value(1), alt.value(0))
                )

                # Draw text labels near the points, and highlight based on selection
                text3 = m1.mark_text(align="left", dx=5, dy=-5).encode(
                    text=alt.condition(nearest1, "rolling_SID:Q", alt.value(" "))
                )

                m2 = (
                    alt.Chart(typhoon_per_year.dropna(axis=0))
                    .mark_area(
                        interpolate="cardinal",
                        line={"color": "#444936"},
                        color=alt.Gradient(
                            gradient="linear",
                            stops=[
                                alt.GradientStop(color="#ADB0B5", offset=0),
                                alt.GradientStop(color="#8BB2BE", offset=1),
                            ],
                            x1=1,
                            x2=1,
                            y1=1,
                            y2=0,
                        ),
                    )
                    .encode(
                        x=alt.X("Year:O"),
                        y=alt.Y("rolling_Land Fall:Q", title="Count"),
                        tooltip=[
                            alt.Tooltip("Year:O", title="Year"),
                            alt.Tooltip("rolling_Land Fall:Q", title="Land Fall"),
                        ],
                    )
                )
                # Draw points on the line, and highlight based on selection
                point4 = m2.mark_point().encode(
                    opacity=alt.condition(nearest1, alt.value(1), alt.value(0))
                )

                # Draw text labels near the points, and highlight based on selection
                text4 = m2.mark_text(align="left", dx=5, dy=-5).encode(
                    text=alt.condition(nearest1, "rolling_Land Fall:Q", alt.value(" "))
                )

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    f'<p align="center">Figure 1. Count of Typhoon Occurence (All Events and Land Fall Events) Within PAR, Per Year</p><br>',
                    unsafe_allow_html=True,
                )
                toggle = st.checkbox("Plot 5-Year Moving Average")

                if toggle:
                    st.altair_chart(
                        (
                            m1
                            + m2
                            + selectors1
                            + rules
                            + point3
                            + point4
                            + text3
                            + text4
                        ),
                        use_container_width=True,
                    )
                else:
                    st.altair_chart(
                        (
                            c1
                            + c2
                            + selectors1
                            + rules
                            + point1
                            + point2
                            + text1
                            + text2
                        ),
                        use_container_width=True,
                    )

                typhoon_per_month = (
                    path_filtered.groupby("Month")
                    .agg({"SID": "count", "Land Fall": "sum"})
                    .sort_index()
                )

                typhoon_per_month = typhoon_per_month.reset_index()

                st.markdown(
                    f"<center>Figure 2. Count of Typhoon Occurence Per Selected Month/s since 1980</center><br>",
                    unsafe_allow_html=True,
                )

                nearest2 = alt.selection(
                    type="single",
                    nearest=True,
                    on="mouseover",
                    fields=["Month"],
                    empty="none",
                )

                selectors2 = (
                    alt.Chart(typhoon_per_month)
                    .mark_point()
                    .encode(x="Month:O", opacity=alt.value(0))
                    .add_selection(nearest2)
                )

                rules1 = (
                    alt.Chart(typhoon_per_month)
                    .mark_rule(color="gray")
                    .encode(x="Month:O",)
                    .transform_filter(nearest2)
                )

                c3 = (
                    alt.Chart(typhoon_per_month)
                    .mark_bar(
                        cornerRadiusTopLeft=5,
                        cornerRadiusTopRight=5,
                        line={"color": "#0A313D"},
                        color=alt.Gradient(
                            gradient="linear",
                            stops=[
                                alt.GradientStop(color="#ADB0B5", offset=0),
                                alt.GradientStop(color="#676E51", offset=1),
                            ],
                            x1=1,
                            x2=1,
                            y1=1,
                            y2=0,
                        ),
                    )
                    .encode(
                        x=alt.X("Month:O"),
                        y=alt.Y("SID:Q", title="Count", axis=alt.Axis(grid=True)),
                        tooltip=[
                            alt.Tooltip("Month:O", title="Month"),
                            alt.Tooltip("SID:Q", title="Total Occurence"),
                        ],
                    )
                )

                # Draw points on the line, and highlight based on selection
                point5 = c3.mark_point(color="#A3AF80").encode(
                    opacity=alt.condition(nearest2, alt.value(1), alt.value(0))
                )

                # Draw text labels near the points, and highlight based on selection
                text5 = c3.mark_text(align="left", dx=5, dy=-5).encode(
                    text=alt.condition(nearest2, "SID:Q", alt.value(" "))
                )

                c4 = (
                    alt.Chart(typhoon_per_month)
                    .mark_area(
                        interpolate="cardinal",
                        line={"color": "#1D3D65"},
                        color=alt.Gradient(
                            gradient="linear",
                            stops=[
                                alt.GradientStop(color="#ADB0B5", offset=0),
                                alt.GradientStop(color="#65828B", offset=1),
                            ],
                            x1=1,
                            x2=1,
                            y1=1,
                            y2=0,
                        ),
                    )
                    .encode(
                        x=alt.X("Month:O", scale=alt.Scale(domain=list(range(1, 13)))),
                        y=alt.Y("Land Fall:Q", title="Count", axis=alt.Axis(grid=True)),
                        tooltip=[
                            alt.Tooltip("Month:O", title="Month"),
                            alt.Tooltip("Land Fall:Q", title="Land Fall"),
                        ],
                    )
                )

                # Draw points on the line, and highlight based on selection
                point6 = c4.mark_point().encode(
                    opacity=alt.condition(nearest2, alt.value(1), alt.value(0))
                )

                # Draw text labels near the points, and highlight based on selection
                text6 = c4.mark_text(align="left", dx=5, dy=-5).encode(
                    text=alt.condition(nearest2, "Land Fall:Q", alt.value(" "))
                )

                st.altair_chart(
                    (c3 + c4 + rules1 + selectors2 + point5 + text5 + point6 + text6),
                    use_container_width=True,
                )

                st.image("./assets/legend1.png")

        elif nav == "Additional Analysis":
            mapping = {"Maximum": "max", "Count": "count"}
            typhoon_agg = st.radio(
                "Select Aggregation Method",
                options=["Maximum", "Count"],
                index=0,
                help="Select the aggregation to be applied for the heatmap. Default is Maximum.",
            )
            typhoon_wind = temp_df.groupby(["Year", "Month"]).agg(
                {"WMO_WIND": mapping[typhoon_agg]}
            )
            typhoon_wind = typhoon_wind.reset_index(level=[0, 1])

            typhoon_wind_heat = typhoon_wind.pivot(
                index="Month", columns="Year", values="WMO_WIND"
            )
            typhoon_wind_heat[typhoon_wind_heat == 0] = np.nan
            typhoon_wind_heat = typhoon_wind_heat.to_numpy()

            x, y = np.meshgrid(range(1980, 2022), range(1, 13))
            source = pd.DataFrame(
                {
                    "Year": x.ravel(),
                    "Month": y.ravel(),
                    f"{typhoon_agg} Winds": typhoon_wind_heat.ravel(),
                }
            )

            c5 = (
                alt.Chart(source)
                .mark_rect()
                .encode(
                    x="Year:O",
                    y="Month:O",
                    color=alt.Color(
                        f"{typhoon_agg} Winds:Q",
                        scale=alt.Scale(scheme="lighttealblue"),
                        legend=alt.Legend(orient="bottom"),
                    ),
                    tooltip=[
                        alt.Tooltip("Year:Q", title="Year"),
                        alt.Tooltip("Month:Q", title="Month"),
                        alt.Tooltip(
                            f"{typhoon_agg} Winds:Q", title=f"{typhoon_agg} Winds"
                        ),
                    ],
                )
            )
            st.markdown(
                f"<center>Figure 3. {typhoon_agg} of Max Sustained Wind (in knots) measurements by Month and Year</center><br>",
                unsafe_allow_html=True,
            )
            st.altair_chart(c5, use_container_width=True)

            # admin['LandFall'] = ''
            # #if the point is within a landmass, add True to Land Fall column, if not, skip.
            # for i in points.index:
            #     for j in admin.index:
            #         if points.loc[i, 'geometry'].intersects(admin.loc[j, 'geometry']):
            #             admin.loc[j,'LandFall'] +=  points.loc[i, 'SID'] + ','
            #             break

            # admin['Count'] = 0
            # for i in admin.index:
            #     admin.loc[i, 'Count'] = len(set(admin.loc[i, 'LandFall'].split(',')))-1

            # first_landfall_points = points.sort_values('ISO_TIME').drop_duplicates(['SID'], keep='first')

            # admin['First LandFall'] = ''
            # #if the point is within a landmass, add True to Land Fall column, if not, skip.
            # for i in first_landfall_points.index:
            #     for j in admin.index:
            #         if first_landfall_points.loc[i, 'geometry'].intersects(admin.loc[j, 'geometry']):
            #             admin.loc[j,'First LandFall'] +=  first_landfall_points.loc[i, 'SID'] + ','
            #             break

            # admin['First LandFall Count'] = 0
            # for i in admin.index:
            #     admin.loc[i, 'First LandFall Count'] = len(set(admin.loc[i, 'First LandFall'].split(',')))-1

            # admin = admin[['NAME_1', 'LandFall', 'Count', 'First LandFall', 'First LandFall Count']]
            # admin.columns = ['Province', 'LandFall', 'Count', 'First LandFall', 'First LandFall Count']
            # admin = admin[admin['Count']>0]

            # admin.to_csv('./assets/typhoon_per_province.csv', index=False)
            st.markdown("<br>", unsafe_allow_html=True)
            fig4 = st.empty()
            admin = read_admin()
            topn, _, _ = st.columns((5, 7, 7))
            with topn:
                n = st.number_input(
                    label='Select Top "N" Provinces',
                    min_value=1,
                    max_value=82,
                    value=10,
                    step=1,
                    help="Select provinces with most number of typhoon land falls. Default is 10.",
                )
            admin = admin.nlargest(int(n), "Count")
            c6 = (
                alt.Chart(admin)
                .mark_bar(
                    cornerRadiusBottomRight=3,
                    cornerRadiusTopRight=3,
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            alt.GradientStop(color="#ADB0B5", offset=0),
                            alt.GradientStop(color="#214F72", offset=1),
                        ],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0,
                    ),
                )
                .encode(
                    y=alt.Y("Province:N", sort="-x"),
                    x=alt.X("Count:Q", title="LandFall"),
                    tooltip=[
                        alt.Tooltip("Province:N", title="Province"),
                        alt.Tooltip("Count:Q", title="LandFall Count"),
                    ],
                )
            )

            c7 = (
                alt.Chart(admin)
                .mark_bar(
                    cornerRadiusBottomRight=3,
                    cornerRadiusTopRight=3,
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            alt.GradientStop(color="#ADB0B5", offset=0),
                            alt.GradientStop(color="#8BB2BE", offset=1),
                        ],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0,
                    ),
                )
                .encode(
                    y=alt.Y("Province:N", title=None, sort="-x"),
                    x=alt.X("First LandFall Count:Q", title="First LandFall"),
                    tooltip=[
                        alt.Tooltip("Province:N", title="Province"),
                        alt.Tooltip(
                            "First LandFall Count:Q", title="Initial Land Fall Count"
                        ),
                    ],
                )
            )

            st.markdown(
                f'<center>Figure 4. Top {int(n)} <i>("N")</i> Province with the Most Number of (First) Land Fall</center><br>',
                unsafe_allow_html=True,
            )
            st.altair_chart((c6 + c7), use_container_width=True)
            st.image("./assets/legend2.png")
            st.markdown("<br>", unsafe_allow_html=True)

        elif nav == "Tabular Datasource":
            st.markdown("---")
            st.markdown("Table 1. Tabular view of the source data.")

            if filter_type == "Spatial-Temporal":
                if temporal_filter == "None":
                    pass

                elif temporal_filter == "By Year":
                    df = df[df["Year"].isin(range(start_year, end_year + 1))]

                elif temporal_filter == "By Month":
                    df = df[
                        df["Month"].isin(
                            range(
                                mapping_dict[start_month], mapping_dict[end_month] + 1
                            )
                        )
                    ]

                elif temporal_filter == "By Date":
                    df = df[
                        (
                            (df["Date"].dt.date >= start_date)
                            & (df["Date"].dt.date <= end_date)
                        )
                    ]

            if filter_type == "Typhoon Name":
                if len(typhoon_filter) == 0:
                    pass
                else:
                    df = df[df["NAME"].isin(typhoon_filter)]

            st.dataframe(df[['SID', 'ISO_TIME', 'NAME', 'NATURE', 'LAT', 'LON', 'WMO_WIND', 'WMO_PRES', 'DIST2LAND', 'LANDFALL', 'STORM_SPD', 'STORM_DR', 'TRACK_TYPE']].sort_values('SID', ascending=False), height=500)

            csv = df.to_csv(index=False).encode("latin-1")
            st.download_button(
                label="Download source data (*.csv)",
                data=csv,
                file_name="typhoon_tracks.csv",
                mime="text/csv",
            )

    elif app == "Earthquake Explorer":
        if nav in ["Dashboard Proper", "Additional Analysis", "Tabular Datasource"]:
            st.title("Earthquake (EQ) Events Explorer")
            st.sidebar.markdown("---")

            with st.sidebar.form(key="update", clear_on_submit=True):
                update_data = st.radio(
                    label="Select data to update", options=["PHIVOLCS", "USGS"], index=0
                )
                password = st.text_input(
                    "Enter password to update data",
                    type="password",
                    help="Warning! This takes at least 1 minute to finish",
                )
                if password == PASSWORD:
                    if update_data == "PHIVOLCS":
                        update_phivolcs()
                    else:
                        update_usgs()
                    st.success("Update successful! Refresh page.")

                elif password == "":
                    pass
                else:
                    st.error("Incorrect password. Try again.")

                submit_button = st.form_submit_button(label="Submit")

        st.markdown("---")
        if nav in ["Dashboard Proper", "Additional Analysis", "Tabular Datasource"]:
            with st.form(key="form", clear_on_submit=False):
                f1, f2, _, f3 = st.columns((1.5, 1.5, 0.2, 3))

                with f1:
                    datasource = st.selectbox(
                        label="Select Data Source",
                        options=["PHIVOLCS", "USGS"],
                        help="Select between two datasource. Default is PHIVOLCS data",
                    )
                    if datasource == "PHIVOLCS":
                        df = read_phivolcs_data()
                        config = read_eq_config("./assets/phivolcs-config.txt")
                    else:
                        df = read_usgs_data()
                        config = read_eq_config("./assets/usgs-config.txt")

                with f2:
                    temporal_filter = st.selectbox(
                        label="Temporal Filter",
                        options=["None", "By Year", "By Month", "By Date"],
                        index=1,
                        help="Filter data by year, month or date. Default is None.",
                    )

                with f3:
                    magnitude_filter_options = np.around(np.arange(1, 9.1, 0.1), 1)
                    magnitude_filter_min, magnitude_filter_max = st.select_slider(
                        label="Magnitude Filter",
                        options=magnitude_filter_options,
                        value=(1, 7),
                        help="Use the slider to select the magnitude.",
                    )
                    df = df[
                        (df["Magnitude"] >= magnitude_filter_min)
                        & (df["Magnitude"] <= magnitude_filter_max)
                    ]

                g1, _, g3 = st.columns((3, 0.3, 2.9))
                if temporal_filter == "None":
                    pass

                elif temporal_filter == "By Year":
                    year_list = np.sort(df["Year"].unique())
                    try:
                        with g1:
                            if datasource == "PHIVOLCS":
                                initial_value = 2017
                            else:
                                initial_value = 1980
                            start_year, end_year = st.select_slider(
                                label="Select Year",
                                options=year_list,
                                value=[initial_value, 2021],
                                help="Use the slider to select start and end year.",
                            )
                        df = df[df["Year"].isin(range(start_year, end_year + 1))]
                    except:
                        st.error("No data based on selection. Refresh app.")
                        return

                elif temporal_filter == "By Month":
                    with g1:
                        start_month, end_month = st.select_slider(
                            label="Select Month",
                            options=month_list,
                            value=["Aug", "Sep"],
                            help="Use the slider to select start and end month.",
                        )

                    df = df[
                        df["Month"].isin(
                            range(
                                mapping_dict[start_month], mapping_dict[end_month] + 1
                            )
                        )
                    ]

                elif temporal_filter == "By Date":
                    date_options = np.sort(df["Date"].unique())
                    with g1:
                        start_date, end_date = st.select_slider(
                            label="Select Date",
                            options=date_options,
                            value=(date_options[0], date_options[-1]),
                            help="Use the slider to select start and end date.",
                        )
                    df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

                with g3:
                    depth_filter_options = range(0, 1110, 10)
                    depth_filter_min, depth_filter_max = st.select_slider(
                        label="Depth Filter",
                        options=depth_filter_options,
                        value=(0, 500),
                        help="Use the slider to select the depth.",
                    )
                    df = df[
                        (df["Depth"] >= depth_filter_min)
                        & (df["Depth"] <= depth_filter_max)
                    ]

                spatial_filter_eq = st.checkbox("Click to enable Spatial Filter")
                if spatial_filter_eq:
                    h1, h2, h3, = st.columns((2, 2, 3))
                    with h1:
                        # loc_button = Button(label="Get Location", default_size=150)
                        # loc_button.js_on_event(ButtonClick, CustomJS(code="""
                        #     navigator.geolocation.getCurrentPosition(
                        #         (loc) => {
                        #             document.dispatchEvent(new CustomEvent("GET_LOCATION", {detail: {lat: loc.coords.latitude, lon: loc.coords.longitude}}))
                        #         }
                        #     )
                        #     """))
                        # result = streamlit_bokeh_events(
                        #     loc_button,
                        #     events="ButtonClick,GET_LOCATION",
                        #     key="get_location",
                        #     refresh_on_update=False,
                        #     override_height=45,
                        #     debounce_time=0)

                        # curlat, curlon = 14.54, 121.05

                        # try:
                        #     if result:
                        #         if "GET_LOCATION" in result:
                        #             curlat = result.get('GET_LOCATION')['lat']
                        #             curlon = result.get('GET_LOCATION')['lon']
                        # except:
                        #     pass
                        lat = st.number_input(
                            label="Latitude",
                            min_value=2.48,
                            max_value=22.09,
                            value=14.654875,
                            step=0.01,
                        )
                    with h2:
                        lon = st.number_input(
                            label="Longitude",
                            min_value=115.64,
                            max_value=129.08,
                            value=121.064653,
                            step=0.01,
                        )

                    coords = pd.DataFrame({"Latitude": [lat], "Longitude": [lon]})

                    with h3:
                        radius = st.number_input(
                            label="Radius (km)",
                            min_value=100,
                            max_value=1000,
                            value=200,
                            step=10,
                        )

                    b = geodesic_point_buffer(lat, lon, radius)
                    crs = pyproj.CRS("EPSG:4326")
                    polygon = gpd.GeoDataFrame(
                        index=[0], crs=crs, geometry=[Polygon(b)]
                    )
                    df = gpd.GeoDataFrame(
                        df, geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"])
                    )
                    df["Buffer"] = 0
                    for i in df.index:
                        for j in polygon.geometry.iteritems():
                            if df.loc[i, "geometry"].within(j[1]):
                                df.loc[i, "Buffer"] = 1
                                break
                    df = df[df["Buffer"] == 1]
                    df = df.drop(["geometry"], axis=1)

                submit_button = st.form_submit_button(label="Run Filter")

            df = df.drop_duplicates()

        if nav == "Dashboard Proper":
            m1, m2, m3, m4 = st.columns(4)
            count = m1.empty()
            eq_count_today = m4.empty()
            latest_magnitude = m3.empty()
            max_magnitude = m2.empty()

            with count:
                st.metric(
                    label="EQ Count",
                    value=millify(df.shape[0], precision=2),
                    delta=f"Latest: {df['Date'].max()}",
                    delta_color="off",
                )


            with eq_count_today:
                new_df = df.copy()
                new_df = df[df["Year"] == df["Year"].max()]
                max_dt = np.sort(new_df["DOY"].unique())
                try:
                    new_eq = new_df[new_df["DOY"] == max_dt[-1]]
                    old_eq = new_df[new_df["DOY"] == max_dt[-2]]

                    st.metric(
                        label=f"EQ Count on {new_eq['Date'].unique().tolist()[0]}",
                        value=millify(new_eq.shape[0], precision=2),
                        delta=f"{(new_eq.shape[0] - old_eq.shape[0])/old_eq.shape[0]:.2%} ({old_eq['Date'].unique().tolist()[0]}: {old_eq.shape[0]})",
                        delta_color="inverse",
                    )
                
                except IndexError:
                    st.metric(
                        label=f"Mean Magnitude",
                        value=millify(df["Magnitude"].mean(), precision=2),
                    )

            with latest_magnitude:
                st.metric(
                    label="Latest EQ Event",
                    value=millify(df["Magnitude"].head(1).squeeze(), precision=2),
                    delta=f'{df["Timestamp"].head(1).squeeze()}',
                    delta_color="off",
                )

            with max_magnitude:
                max_mag = df["Magnitude"].max()
                st.metric(
                    label="Strongest EQ Event",
                    value=millify(max_mag, precision=2),
                    delta=f'Occurence: {millify(np.sum(df["Magnitude"]==max_mag), precision=2)}',
                    delta_color="off",
                )

            keplergl_df = df[
                ["Timestamp", "Latitude", "Longitude", "Magnitude", "Depth", "Location"]
            ]
            try:
                keplergl_df['Timestamp'] = keplergl_df['Timestamp'].dt.strftime("%Y-%m-%dT%I:%M:%S %p")
            except:
                pass
            eq_map = KeplerGl()
            eq_map.config = config
            eq_map.add_data(data=keplergl_df, name="EQ")
            if spatial_filter_eq:
                config['config']['mapState']['latitude'] = lat
                config['config']['mapState']['longitude'] = lon
                config['config']['mapState']['zoom'] = 6
                eq_map.add_data(data=polygon, name="Buffer")
                eq_map.add_data(data=coords, name="Loc")
            keplergl_static(eq_map)

            eq_map.save_to_html()
            download_file = codecs.open('keplergl_map.html', 'r', 'utf-8').read()

            st.download_button(label='Download interactive map', data=download_file,                 
                        file_name="eq-events.html",
                        mime="text/html")

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("Click to hide/view visualizations", expanded=True):
                agg = {
                    "None": "Year",
                    "By Year": "Year",
                    "By Month": "Month",
                    "By Date": "Date",
                }
                if temporal_filter == "By Date":
                    agg_type = "T"
                    tooltip_agg_type = "T"
                else:
                    agg_type = "O"
                    tooltip_agg_type = "Q"

                nearest1 = alt.selection(
                    type="single",
                    nearest=False,
                    on="mouseover",
                    fields=[f"{agg[temporal_filter]}"],
                    empty="none",
                )

                selectors1 = (
                    alt.Chart(df)
                    .mark_point()
                    .encode(
                        x=f"{agg[temporal_filter]}:{agg_type}", opacity=alt.value(0)
                    )
                    .add_selection(nearest1)
                )

                rules1 = (
                    alt.Chart(df)
                    .mark_rule(color="gray", opacity=0.8)
                    .encode(x=f"{agg[temporal_filter]}:{agg_type}",)
                    .transform_filter(nearest1)
                )

                # Selectbox of Date, Month, Year
                if temporal_filter == "By Date":
                    c2 = (
                        alt.Chart(df)
                        .mark_area(
                            line={"color": "#444936"},
                            color=alt.Gradient(
                                gradient="linear",
                                stops=[
                                    alt.GradientStop(color="#ADB0B5", offset=0),
                                    alt.GradientStop(color="#D9D9C2", offset=1),
                                ],
                                x1=1,
                                x2=1,
                                y1=1,
                                y2=0,
                            ),
                        )
                        .encode(
                            x=alt.X(f"{agg[temporal_filter]}:{agg_type}"),
                            y=alt.Y("count(Magnitude):Q"),
                            tooltip=[
                                (f"{agg[temporal_filter]}:{tooltip_agg_type}"),
                                "count(Magnitude)",
                            ],
                        )
                    )
                else:
                    c2 = (
                        alt.Chart(df)
                        .mark_bar(
                            cornerRadiusTopLeft=5,
                            cornerRadiusTopRight=5,
                            # interpolate="cardinal",
                            line={"color": "#444936"},
                            color=alt.Gradient(
                                gradient="linear",
                                stops=[
                                    alt.GradientStop(color="#ADB0B5", offset=0),
                                    alt.GradientStop(color="#D9D9C2", offset=1),
                                ],
                                x1=1,
                                x2=1,
                                y1=1,
                                y2=0,
                            ),
                        )
                        .encode(
                            x=alt.X(f"{agg[temporal_filter]}:{agg_type}"),
                            y=alt.Y("count(Magnitude):Q"),
                            tooltip=[
                                (f"{agg[temporal_filter]}:{tooltip_agg_type}"),
                                "count(Magnitude)",
                            ],
                        )
                    )

                # Draw points on the line, and highlight based on selection
                point1 = c2.mark_point(color="#A3AF80").encode(
                    opacity=alt.condition(nearest1, alt.value(1), alt.value(0))
                )

                # Draw text labels near the points, and highlight based on selection
                text1 = c2.mark_text(align="left", dx=5, dy=-5).encode(
                    text=alt.condition(nearest1, "count(Magnitude):Q", alt.value(" "))
                )

                st.markdown(
                    f'<p align="center">Figure 1. Count of Earthquake Events, Per {agg[temporal_filter]}</p><br>',
                    unsafe_allow_html=True,
                )

                st.altair_chart(
                    (c2 + selectors1 + rules1 + point1 + text1),
                    use_container_width=True,
                )

                st.markdown(
                    f'<p align="center">Figure 2. Distribution of Earthquake Event Magnitude</p><br>',
                    unsafe_allow_html=True,
                )

                nearest2 = alt.selection(
                    type="single",
                    nearest=True,
                    on="mouseover",
                    fields=["Magnitude"],
                    empty="none",
                )

                selectors2 = (
                    alt.Chart(df)
                    .mark_point()
                    .encode(x="Magnitude:Q", opacity=alt.value(0))
                    .add_selection(nearest2)
                )

                rules2 = (
                    alt.Chart(df)
                    .mark_rule(color="#838479", opacity=0.2, strokeWidth=0.5)
                    .encode(x="Magnitude:Q",)
                    .transform_filter(nearest2)
                )

                c3 = (
                    alt.Chart(df)
                    .mark_area(opacity=0.6, interpolate="monotone", color="#C3C5BC")
                    .encode(
                        x=alt.X("Magnitude:Q", stack=None),
                        y=alt.Y("count()", stack=None),
                        tooltip=["Magnitude", "count()"]
                        # color=alt.Color('Year:O', legend=None)
                    )
                )

                cdf = Cdf.from_seq(df['Magnitude'])
                cdf = pd.DataFrame({'Magnitude':cdf.qs, 'Percentile':np.round(cdf.ps, 3)})
                c3a = (
                    alt.Chart(cdf)
                    .mark_area(opacity=0.6, interpolate="monotone", color="#C3C5BC")
                    .encode(
                        x=alt.X("Magnitude:Q", stack=None),
                        y=alt.Y("Percentile:Q", stack=None),
                        tooltip=["Magnitude", "Percentile"]
                        # color=alt.Color('Year:O', legend=None)
                    )
                )

                pmf = Pmf.from_seq(df['Magnitude'])
                pmf = pd.DataFrame({'Magnitude':pmf.qs, 'Percentile':np.round(pmf.ps, 3)})
                c3b = (
                    alt.Chart(pmf)
                    .mark_area(opacity=0.6, interpolate="monotone", color="#C3C5BC")
                    .encode(
                        x=alt.X("Magnitude:Q", stack=None),
                        y=alt.Y("Percentile:Q", stack=None),
                        tooltip=["Magnitude", "Percentile"]
                        # color=alt.Color('Year:O', legend=None)
                    )
                )

                rule = (
                    alt.Chart(df)
                    .mark_rule(color="#838479")
                    .encode(x=alt.X("mean(Magnitude):Q"))
                )

                # Draw points on the line, and highlight based on selection
                point2 = c3.mark_point(color="#A3AF80").encode(
                    opacity=alt.condition(nearest2, alt.value(1), alt.value(0))
                )

                point2a = c3a.mark_point(color="#A3AF80").encode(
                    opacity=alt.condition(nearest2, alt.value(1), alt.value(0))
                )

                point2b = c3b.mark_point(color="#A3AF80").encode(
                    opacity=alt.condition(nearest2, alt.value(1), alt.value(0))
                )

                # Draw text labels near the points, and highlight based on selection
                text2 = c3.mark_text(align="left", dx=5, dy=-5).encode(
                    text=alt.condition(nearest2, "count()", alt.value(" "))
                )

                text2a = c3a.mark_text(align="left", dx=5, dy=-5).encode(
                    text=alt.condition(nearest2, "Percentile:Q", alt.value(" "))
                )

                text2b = c3b.mark_text(align="left", dx=5, dy=-5).encode(
                    text=alt.condition(nearest2, "Percentile:Q", alt.value(" "))
                )

                dist = st.radio(label='Distribution', options=['Histogram', 'PDF', 'CDF'], help='PMF - Probability Mass Function; CDF - Cumulative Density Function')

                if dist == 'Histogram':
                    st.altair_chart(
                        c3 + rule + rules2 + selectors2 + point2 + text2,
                        use_container_width=True,
                    )
                elif dist == 'PDF':
                    st.altair_chart(
                        c3b + rule + rules2 + selectors2 + point2b + text2b,
                        use_container_width=True,
                    )
                else:
                    st.altair_chart(
                        c3a + rule + rules2 + selectors2 + point2a + text2a,
                        use_container_width=True,
                    )

        elif nav == "Additional Analysis":
            st.markdown("<br>", unsafe_allow_html=True)
            c1 = (
                alt.Chart(df)
                .mark_circle(size=60, opacity=0.3)
                .encode(
                    x=alt.X("Magnitude:Q"),
                    y=alt.Y("Depth:Q", title="Depth (m)"),
                    color=alt.Color(
                        "Year:O", legend=None, scale=alt.Scale(scheme="lighttealblue")
                    ),
                    tooltip=["Date", "Magnitude", "Depth"],
                )
            )  # .properties(width=600)

            # top_hist = alt.Chart(df).mark_area(opacity=.3, interpolate='monotone').encode(
            #     x=alt.X('Magnitude:Q', bin=alt.Bin(maxbins=20), stack=None, title=''),
            #     y=alt.Y('count()', stack=None, title='')
            # ).properties(height=60, width=600)

            # right_hist = alt.Chart(df).mark_area(opacity=.3, interpolate='monotone').encode(
            #     x=alt.X('Depth:Q', bin=alt.Bin(maxbins=20), stack=None, title=''),
            #     y=alt.Y('count()', stack=None, title='')
            # ).properties(width=60)

            st.markdown(
                f"<center>Figure 3. Relationship between Depth (in m) and Magnitude of Earthquakes</center><br>",
                unsafe_allow_html=True,
            )
            st.altair_chart(c1, use_container_width=True)

            mapping = {"Maximum": "max", "Count": "count"}
            heat_func = st.radio(
                "Select Aggregation Method",
                options=["Maximum", "Count"],
                index=0,
                help="Select the aggregation to be applied for the heatmap. Default is Maximum.",
            )
            heat_df = df.groupby(["Year", "Month"]).agg(
                {"Magnitude": mapping[heat_func]},
            )
            heat_df = heat_df.reset_index(level=[0, 1])
            heat_df = heat_df.pivot(index="Month", columns="Year", values="Magnitude")
            heat_df[heat_df.isna()] = 0
            heat_df = heat_df.to_numpy()

            x, y = np.meshgrid(
                np.sort(df["Year"].unique()), np.sort(df["Month"].unique())
            )
            source = pd.DataFrame(
                {
                    "Year": x.ravel(),
                    "Month": y.ravel(),
                    f"{heat_func} EQ": heat_df.ravel(),
                }
            )

            c4 = (
                alt.Chart(source)
                .mark_rect()
                .encode(
                    x="Year:O",
                    y="Month:O",
                    color=alt.Color(
                        f"{heat_func} EQ:Q",
                        scale=alt.Scale(scheme="lighttealblue"),
                        legend=alt.Legend(orient="bottom"),
                    ),
                    tooltip=[
                        alt.Tooltip("Year:Q", title="Year"),
                        alt.Tooltip("Month:Q", title="Month"),
                        alt.Tooltip(f"{heat_func} EQ:Q", title=f"{heat_func} EQ"),
                    ],
                )
            )
            st.markdown(
                f"<center>Figure 4. {heat_func} of Earthquake Magnitude by Month and Year</center><br>",
                unsafe_allow_html=True,
            )
            st.altair_chart(c4, use_container_width=True)

            c5 = (
                alt.Chart(df)
                .mark_boxplot(
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            alt.GradientStop(color="#376E98", offset=0),
                            alt.GradientStop(color="#6AA3B6", offset=1),
                        ],
                        x1=1,
                        x2=1,
                        y1=1,
                        y2=0,
                    )
                )
                .encode(y=alt.Y("Month:O"), x=alt.X("sum(Magnitude):Q"),)
            )
            st.markdown(
                f"<center>Figure 5. Distribution of Earthquake Magnitude per Month</center><br>",
                unsafe_allow_html=True,
            )
            st.altair_chart(c5, use_container_width=True)

        elif nav == "Tabular Datasource":
            st.markdown("---")
            st.markdown("Table 1. Tabular view of the source data.")
            st.dataframe(df[['Timestamp', 'Latitude', 'Longitude', 'Depth', 'Magnitude', 'Location']], height=500)

            csv = df.to_csv(index=False).encode("latin-1")
            st.download_button(
                label="Download source data (*.csv)",
                data=csv,
                file_name="eq-events.csv",
                mime="text/csv",
            )

    if nav == "Discussion Board":
        st.markdown(
            f"""
        Post your ideas here, provide feedback on the app and/or share the results of your exploration.
        """,
            unsafe_allow_html=True,
        )

        placeholder = st.empty()
        with st.spinner(text="Loading the discussion board..."):
            components.iframe(
                "https://padlet.com/kaquisado/qpefyhsb84m1ut0c", height=800
            )
        time.sleep(5)

        placeholder.success("Done!")
        time.sleep(0.5)
        placeholder.empty()
        return

    elif nav == "About QT Explorer":
        st.markdown(
            f"""
        ### Earthquake (EQ) Events Explorer
        <p align="justify">The web app aims to visualize the earthquake events that occurred within Philippine archipelago as recorded by the <a href="https://www.phivolcs.dost.gov.ph/">Philippine Institute of Volcanology and Seismology (PHIVOLCS)</a> (2017-present) and the <a href="https://earthquake.usgs.gov/">United States Geological Survey (USGS)</a> (1910-present). The data contains historical earthquake events information such as location, magnitude, depth, among others, in CSV format.<br>
        <br>The web app is designed to be interactive with features that enable users to drill down into the data by selecting their preferred attributes, such as the source of data, temporal filters, magnitude, and depth filters, to answer specific questions one might have. 
        </justify>""",
            unsafe_allow_html=True,
        )

        # st.image('./assets/earthquake-dashboard.png', use_column_width=True)

        st.markdown("---")
        st.markdown(
            f"""
        ### Typhoon Track Explorer:
        <p align="justify">The web app aims to visualize the typhoon tracks that entered the Philippine Area of Responsibility (PAR) dated 1980 - present. The data was downloaded from National Oceanic and Atmospheric Administration's (NOAA) <a href="https://www.ncdc.noaa.gov/ibtracs/index.php?name=ib-v4-access">International Best Track for Climate Stewardship (IBTrACS)</a>. The data contains three-hourly (3H) information of the location, maximum winds, pressure, among others of all known typhoons, in CSV format.<br><br>
        The web app is interactive. It has a control panel that enables users to drill down into the data by selecting their preferred filters. For example, users can opt to filter the data using the temporal filters (month, year, or date), spatial filters (using provincial boundaries), and typhoon name filters (International name) to answer specific questions one might have.</justify>
        """,
            unsafe_allow_html=True,
        )
        now = datetime.now().strftime("%d %B %Y")
        # st.image('./assets/typhoon-dashboard.png', use_column_width=True)
        st.markdown("---")
        st.markdown(
            f"""
        ### Resources:<br>
        <ul>
        <li style="list-style-type:square">IBTrACS - International Best Track Archive for Climate Stewardship. (2021). Retrieved 15 September 2021. Accessed <a href='https://www.ncdc.noaa.gov/ibtracs/index.php?name=ib-v4-access'>here</a>.</li>
        <li style="list-style-type:square">Philippine Area of Responsibility (PAR) Polygon - Humanitarian Data Exchange. (2021). Retrieved 15 September 2021. Accessed <a href='https://data.humdata.org/dataset/philippine-area-of-responsibility-par-polygon'>here</a>.</li>
        <li style="list-style-type:square">Typhoons in the Philippines - Wikipedia. (2021). Retrieved 15 September 2021. Accessed <a href="https://en.wikipedia.org/wiki/Typhoons_in_the_Philippines">here</a>.</li>
        <li style="list-style-type:square">Search Earthquake Catalog. ({datetime.now().year}). Retrieved {now}. Accessed <a href='https://earthquake.usgs.gov/earthquakes/search/'>here</a>.</li>
        <li style="list-style-type:square">Seismological Observation and Earthquake Prediction Division. ({datetime.now().year}). Retrieved {now}. Accessed <a href='https://earthquake.phivolcs.dost.gov.ph/'>here</a>.</li>
        </ul>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.subheader("Team:")
        _, author1, _, author2, _ = st.columns((2, 3, 1, 3, 2))
        st.markdown("<br><br>", unsafe_allow_html=True)
        author1.image(r"./assets/author1.png")
        author1.markdown(
            f"""<center>
            <h3>Kenneth A. Quisado</h3>
            kaquisado@gmail.com<br>
            <a href="https://www.linkedin.com/in/kaquisado/">LinkedIn</a> <a href="https://github.com/kenquix">GitHub</a></center>
        """,
            unsafe_allow_html=True,
        )
        author1.markdown("---")
        author1.markdown(
            f"""
            <center>Remote sensing. Python. Cat person.</center><br><br>
        """,
            unsafe_allow_html=True,
        )

        author2.image(r"./assets/author2.png")
        author2.markdown(
            f"""
            <center><h3>Ma. Verlina E. Tonga</h3>
            foresterverlinatonga@gmail.com<br>
            <a href="https://www.linkedin.com/in/ma-verlina-tonga-444562a4/">LinkedIn</a> <a href="https://github.com/kenquix">GitHub</a>
        </center>""",
            unsafe_allow_html=True,
        )
        author2.markdown("---")
        author2.markdown(
            f"""
            <center>Forester. Environment Planner.</center>
        """,
            unsafe_allow_html=True,
        )

if __name__ == "__main__":
    main()
