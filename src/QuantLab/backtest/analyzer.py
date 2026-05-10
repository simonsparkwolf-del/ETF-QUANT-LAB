from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch


class BacktestAnalyzer:
    def __init__(self, save_path: Path, run_name: str, save_artifacts: bool = True):
        self.save_path = save_path
        safe_name = run_name.strip().replace(" ", "_")
        self.run_name = safe_name if safe_name else "backtest"
        self.etf_cmap = "tab20"
        self.heatmap_cmap = "RdYlBu_r"
        self.output_small_charts = False
        self.save_artifacts = save_artifacts

    def _out_path(self, filename: str) -> Path:
        return self.save_path / f"{self.run_name}_{filename}"

    def _infer_periods_per_year(self, dates: pd.Series) -> int:
        unique_dates = pd.to_datetime(dates).sort_values().drop_duplicates()
        if len(unique_dates) < 3:
            return 252
        median_days = unique_dates.diff().dt.days.dropna().median()
        if pd.isna(median_days) or median_days <= 0:
            return 252
        return int(round(365 / median_days))

    @staticmethod
    def _calc_turnover(
        holding_history: pd.DataFrame,
        value_history: pd.DataFrame,
        periods_per_year: int,
    ) -> tuple[float, float]:
        """
        Per-period turnover = sum_i |ΔMV_i| / (2 * total_value), averaged across rebalance dates;
        turnover_annualized = mean * periods_per_year.
        """
        if holding_history.empty or len(value_history) < 2:
            return 0.0, 0.0
        hh = holding_history.copy()
        hh["mv"] = hh["volume"].astype(float) * hh["market_price"].astype(float)
        hh["signed_mv"] = np.where(hh["direction"] == "short", -hh["mv"].abs(), hh["mv"].abs())
        pivot = hh.pivot_table(index="date", columns="ticker", values="signed_mv", aggfunc="sum", fill_value=0.0)
        pivot = pivot.sort_index()
        vh_dates = pd.to_datetime(value_history["date"]).sort_values().drop_duplicates()
        pivot = pivot.reindex(vh_dates, fill_value=0.0)
        equity_series = (
            pd.to_datetime(value_history["date"])
            .pipe(lambda s: value_history.assign(_d=s).set_index("_d")["total_value"].astype(float))
            .reindex(pivot.index)
        )
        delta_abs = pivot.diff().abs().sum(axis=1)
        denom = 2.0 * equity_series.replace(0.0, np.nan)
        turnover_t = delta_abs / denom
        turnover_t = turnover_t.iloc[1:].replace([np.inf, -np.inf], np.nan).dropna()
        if turnover_t.empty:
            return 0.0, 0.0
        avg_turn = float(turnover_t.mean())
        return avg_turn, float(avg_turn * periods_per_year)

    def _calc_metrics(self, value_history: pd.DataFrame, holding_history: pd.DataFrame | None = None) -> dict[str, float | int]:
        value_history = value_history.sort_values("date").copy()
        value_history["date"] = pd.to_datetime(value_history["date"])
        equity = value_history["total_value"].astype(float)
        returns = equity.pct_change().replace([np.inf, -np.inf], np.nan).dropna()

        if returns.empty:
            periods_per_year = self._infer_periods_per_year(cast(pd.Series, value_history["date"]))
            hh_empty = pd.DataFrame() if holding_history is None else holding_history
            turnover_avg, turnover_ann = BacktestAnalyzer._calc_turnover(
                hh_empty, value_history, periods_per_year
            )
            return {
                "start_value": float(equity.iloc[0]),
                "end_value": float(equity.iloc[-1]),
                "total_return": 0.0,
                "annual_return": 0.0,
                "annual_volatility": 0.0,
                "sharpe": 0.0,
                "max_drawdown": 0.0,
                "turnover_avg_period": turnover_avg,
                "turnover_annualized": turnover_ann,
                "win_rate": 0.0,
                "periods_per_year": int(periods_per_year),
                "num_periods": int(len(equity)),
            }

        periods_per_year = self._infer_periods_per_year(cast(pd.Series, value_history["date"]))
        hh = pd.DataFrame() if holding_history is None else holding_history
        turnover_avg, turnover_ann = self._calc_turnover(hh, value_history, periods_per_year)
        win_rate = float((returns > 0).mean())
        total_return = equity.iloc[-1] / equity.iloc[0] - 1.0
        annual_return = (1.0 + total_return) ** (periods_per_year / len(returns)) - 1.0
        annual_volatility = returns.std(ddof=1) * np.sqrt(periods_per_year)
        returns_std = returns.std(ddof=1)
        sharpe = 0.0
        if returns_std > 0:
            sharpe = float(returns.mean() / returns_std * np.sqrt(periods_per_year))

        nav = equity / equity.iloc[0]
        drawdown = nav / nav.cummax() - 1.0
        max_drawdown = float(drawdown.min())

        return {
            "start_value": float(equity.iloc[0]),
            "end_value": float(equity.iloc[-1]),
            "total_return": float(total_return),
            "annual_return": float(annual_return),
            "annual_volatility": float(annual_volatility),
            "sharpe": sharpe,
            "max_drawdown": max_drawdown,
            "turnover_avg_period": turnover_avg,
            "turnover_annualized": turnover_ann,
            "win_rate": win_rate,
            "periods_per_year": int(periods_per_year),
            "num_periods": int(len(equity)),
        }

    @staticmethod
    def _fmt_pct(value: float) -> str:
        return f"{value * 100:.2f}%"

    @staticmethod
    def _fmt_num(value: float) -> str:
        return f"{value:,.2f}"

    def _write_metrics_markdown(self, metrics: dict[str, float | int]) -> None:
        start_value = float(metrics["start_value"])
        end_value = float(metrics["end_value"])
        total_return = float(metrics["total_return"])
        annual_return = float(metrics["annual_return"])
        annual_volatility = float(metrics["annual_volatility"])
        sharpe = float(metrics["sharpe"])
        max_drawdown = float(metrics["max_drawdown"])
        turnover_avg = float(metrics["turnover_avg_period"])
        turnover_ann = float(metrics["turnover_annualized"])
        win_rate = float(metrics["win_rate"])
        periods_per_year = int(metrics["periods_per_year"])
        num_periods = int(metrics["num_periods"])

        markdown = (
            "# Backtest Metrics Report\n\n"
            "## Core Metrics\n"
            f"- Start Value: `{self._fmt_num(start_value)}`\n"
            f"- End Value: `{self._fmt_num(end_value)}`\n"
            f"- Total Return: `{self._fmt_pct(total_return)}`\n"
            f"- Annual Return: `{self._fmt_pct(annual_return)}`\n"
            f"- Annual Volatility: `{self._fmt_pct(annual_volatility)}`\n"
            f"- Sharpe Ratio: `{sharpe:.3f}`\n"
            f"- Max Drawdown: `{self._fmt_pct(max_drawdown)}`\n"
            f"- Turnover (avg per period): `{self._fmt_pct(turnover_avg)}` — sum(|Δ signed MV|) / (2 × total_value), by date\n"
            f"- Turnover (annualized): `{self._fmt_pct(turnover_ann)}` — avg per period × periods_per_year\n"
            f"- Win Rate: `{self._fmt_pct(win_rate)}` — share of periods with positive total_value return\n"
            f"- Periods Per Year: `{periods_per_year}`\n"
            f"- Number of Periods: `{num_periods}`\n\n"
            "## Exposure Notes\n"
            "- `Exposure` means the portfolio's market value exposure to risk.\n"
            "- In this implementation, `long` exposure is positive and `short` exposure is negative.\n"
            "- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.\n"
            "- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.\n\n"
            "## Output Files\n"
            f"- `{self.run_name}_metrics.json`: machine-readable metrics\n"
            f"- `{self.run_name}_metrics.md`: human-readable metrics summary\n"
            f"- `{self.run_name}_value_history.csv`: portfolio value time series\n"
            f"- `{self.run_name}_holding_history.csv`: position snapshots\n"
            f"- `{self.run_name}_all_in_one_panel.png`: high-resolution all-in-one dashboard\n"
        )
        self._out_path("metrics.md").write_text(markdown, encoding="utf-8")

    @staticmethod
    def _style_date_axis(ax) -> None:
        locator = mdates.AutoDateLocator(minticks=4, maxticks=10)
        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        ax.tick_params(axis="x", labelrotation=0)

    def evaluate(self, value_records: list[dict], holding_records: list[dict]) -> dict[str, float | int]:
        value_history = pd.DataFrame.from_records(value_records)
        holding_history = pd.DataFrame.from_records(holding_records)
        if value_history.empty:
            return {}

        value_history = value_history.sort_values("date").copy()
        value_history["date"] = pd.to_datetime(value_history["date"])
        if not holding_history.empty:
            holding_history = holding_history.copy()
            holding_history["date"] = pd.to_datetime(holding_history["date"])

        hh_for_metrics = holding_history if not holding_history.empty else pd.DataFrame()
        metrics = self._calc_metrics(value_history, hh_for_metrics)

        if not self.save_artifacts:
            return metrics

        self.save_path.mkdir(parents=True, exist_ok=True)
        value_history.to_csv(self._out_path("value_history.csv"), index=False)
        if not holding_history.empty:
            holding_history.to_csv(self._out_path("holding_history.csv"), index=False)

        with open(self._out_path("metrics.json"), "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        self._write_metrics_markdown(metrics)

        # Asset/liability trajectory report for value history.
        value_components = value_history.loc[:, ["date", "cash", "securities_value", "liability_value", "total_value"]].copy()
        value_components = value_components.sort_values("date")
        value_components["liability_value"] = -value_components["liability_value"].abs()

        fig_comp, axes_comp = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        ax_comp_top = axes_comp[0]
        ax_comp_bottom = axes_comp[1]

        # Top panel: component trajectories without fill.
        dates = value_components["date"]
        cash_values = value_components["cash"].astype(float)
        security_values = value_components["securities_value"].astype(float)
        liability_values = value_components["liability_value"].astype(float)  # already negative

        ax_comp_top.plot(dates, cash_values, color="#7f7f7f", linewidth=1.8, label="Cash")
        ax_comp_top.plot(dates, security_values, color="#2ca02c", linewidth=1.8, label="Securities")
        ax_comp_top.plot(dates, liability_values, color="#d62728", linewidth=1.8, label="Liability (negative)")
        ax_comp_top.axhline(0.0, color="black", linewidth=0.8, alpha=0.8)
        ax_comp_top.set_title("Asset / Liability Component Trajectories")
        ax_comp_top.set_ylabel("Value")
        ax_comp_top.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.0f}"))
        ax_comp_top.grid(color="black", linewidth=0.4, alpha=0.25)
        ax_comp_top.legend(loc="upper left")

        # Bottom panel: total value trajectory for direct reading.
        ax_comp_bottom.plot(dates, value_components["total_value"], label="Total Value", color="#1f77b4", linewidth=2.1)
        ax_comp_bottom.set_title("Total Value Trajectory")
        ax_comp_bottom.set_xlabel("Date")
        ax_comp_bottom.set_ylabel("Total Value")
        ax_comp_bottom.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.0f}"))
        ax_comp_bottom.grid(color="black", linewidth=0.4, alpha=0.25)
        ax_comp_bottom.legend(loc="upper left")
        self._style_date_axis(ax_comp_bottom)

        fig_comp.tight_layout()
        if self.output_small_charts:
            fig_comp.savefig(self._out_path("asset_liability_trajectory.png"), dpi=150)
        plt.close(fig_comp)

        equity = value_history["total_value"].astype(float)
        drawdown = equity / equity.cummax() - 1.0

        plt.style.use("seaborn-v0_8-whitegrid")
        holding = None
        net_exposure_series = None
        if not holding_history.empty:
            holding = holding_history.copy()
            holding["market_value"] = holding["volume"].astype(float) * holding["market_price"].astype(float)
            holding["signed_market_value"] = np.where(
                holding["direction"] == "short",
                -holding["market_value"].abs(),
                holding["market_value"].abs(),
            )
            net_exposure = holding.groupby("date", as_index=False).agg({"signed_market_value": "sum"})
            net_exposure["date"] = pd.to_datetime(net_exposure["date"])
            net_exposure_series = net_exposure.sort_values("date")

            fig2, ax2 = plt.subplots(figsize=(12, 4))
            ax2.plot(net_exposure_series["date"], net_exposure_series["signed_market_value"], color="#9467bd", linewidth=2)
            ax2.axhline(0.0, color="black", linewidth=0.8, alpha=0.8)
            ax2.set_title("Net Holding Exposure")
            ax2.set_xlabel("Date")
            ax2.set_ylabel("Exposure")
            ax2.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.0f}"))
            ax2.grid(color="black", linewidth=0.4, alpha=0.25)
            self._style_date_axis(ax2)
            fig2.tight_layout()
            if self.output_small_charts:
                fig2.savefig(self._out_path("holding_exposure.png"), dpi=150)
            plt.close(fig2)

        # Value history report now includes net exposure panel.
        panel_count = 3 if net_exposure_series is not None else 2
        fig, axes = plt.subplots(panel_count, 1, figsize=(12, 10 if panel_count == 3 else 8), sharex=True)
        if panel_count == 2:
            axes = np.array(axes)
        axes[0].plot(value_history["date"], equity, label="Total Value", color="#1f77b4", linewidth=2)
        axes[0].set_title("Total Value")
        axes[0].set_ylabel("Total Value")
        axes[0].legend(loc="upper left")
        axes[0].grid(color="black", linewidth=0.4, alpha=0.25)

        axes[1].fill_between(value_history["date"], drawdown, 0.0, color="#d62728", alpha=0.28)
        axes[1].set_title("Drawdown")
        axes[1].set_ylabel("Drawdown")
        axes[1].yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y * 100:.1f}%"))
        axes[1].grid(color="black", linewidth=0.4, alpha=0.25)

        if panel_count == 3 and net_exposure_series is not None:
            axes[2].plot(net_exposure_series["date"], net_exposure_series["signed_market_value"], color="#9467bd", linewidth=2)
            axes[2].axhline(0.0, color="black", linewidth=0.8, alpha=0.8)
            axes[2].set_title("Net Exposure")
            axes[2].set_ylabel("Exposure")
            axes[2].set_xlabel("Date")
            axes[2].yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.0f}"))
            axes[2].grid(color="black", linewidth=0.4, alpha=0.25)
            self._style_date_axis(axes[2])
        else:
            axes[1].set_xlabel("Date")
            self._style_date_axis(axes[1])

        fig.tight_layout()
        if self.output_small_charts:
            fig.savefig(self._out_path("value_history.png"), dpi=150)
        plt.close(fig)

        if (
            "long_fee_rate_cum" in value_history.columns
            and "short_fee_rate_cum" in value_history.columns
            and "long_fee_cum" in value_history.columns
            and "short_fee_cum" in value_history.columns
        ):
            fig_fee, axes_fee = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
            ax_fee_amt = axes_fee[0]
            ax_fee_rate = axes_fee[1]

            # Top panel: cumulative fee amount.
            ax_fee_amt.plot(
                value_history["date"],
                value_history["long_fee_cum"].astype(float),
                color="#2ca02c",
                linewidth=1.9,
                label="Long Cumulative Fee Amount",
            )
            ax_fee_amt.plot(
                value_history["date"],
                value_history["short_fee_cum"].astype(float),
                color="#d62728",
                linewidth=1.9,
                label="Short Cumulative Fee Amount",
            )
            ax_fee_amt.set_title("Cumulative Trading Fee Amount")
            ax_fee_amt.set_ylabel("Amount")
            ax_fee_amt.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.2f}"))
            ax_fee_amt.grid(color="black", linewidth=0.4, alpha=0.25)
            ax_fee_amt.legend(loc="upper left")

            # Bottom panel: cumulative fee rate.
            ax_fee_rate.plot(
                value_history["date"],
                value_history["long_fee_rate_cum"].astype(float),
                color="#2ca02c",
                linewidth=1.9,
                label="Long Cumulative Fee Rate",
            )
            ax_fee_rate.plot(
                value_history["date"],
                value_history["short_fee_rate_cum"].astype(float),
                color="#d62728",
                linewidth=1.9,
                label="Short Cumulative Fee Rate",
            )
            ax_fee_rate.set_title("Cumulative Trading Fee Rate")
            ax_fee_rate.set_xlabel("Date")
            ax_fee_rate.set_ylabel("Fee Rate")
            ax_fee_rate.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y * 100:.2f}%"))
            ax_fee_rate.grid(color="black", linewidth=0.4, alpha=0.25)
            self._style_date_axis(ax_fee_rate)
            ax_fee_rate.legend(loc="upper left")

            fig_fee.tight_layout()
            if self.output_small_charts:
                fig_fee.savefig(self._out_path("fee_rate_cumulative.png"), dpi=150)
            plt.close(fig_fee)

        if holding is None:
            return metrics

        heatmap_data = holding.pivot_table(
            index="ticker",
            columns="date",
            values="signed_market_value",
            aggfunc="sum",
            fill_value=0.0,
        )
        if not heatmap_data.empty:
            fig3, ax3 = plt.subplots(figsize=(14, 6))
            ax3.set_facecolor("white")
            ax3.set_title("Holding Exposure Heatmap (Ticker x Date)")
            ax3.set_xlabel("Date")
            ax3.set_ylabel("Ticker")
            rows, cols = heatmap_data.shape
            values = heatmap_data.to_numpy(dtype=float)
            vmax = float(np.max(np.abs(values)))
            if vmax < 1e-12:
                vmax = 1.0

            # White grid only (no background fill), with fixed-size square markers.
            x_centers = np.arange(cols) + 0.5
            y_centers = np.arange(rows) + 0.5
            xx, yy = np.meshgrid(x_centers, y_centers)
            flat_values = values.reshape(-1)
            non_zero_mask = np.abs(flat_values) > 1e-12
            sc = ax3.scatter(
                xx.reshape(-1)[non_zero_mask],
                yy.reshape(-1)[non_zero_mask],
                c=flat_values[non_zero_mask],
                cmap=self.heatmap_cmap,
                vmin=-vmax,
                vmax=vmax,
                s=95.0,
                marker="s",
                linewidths=0.0,
            )

            # Keep every cell equal-width and align ticks at cell centers.
            ax3.set_xlim(0, cols)
            ax3.set_ylim(rows, 0)
            heatmap_dates = pd.to_datetime(heatmap_data.columns)
            tick_count = min(10, cols)
            tick_idx = np.linspace(0, cols - 1, num=tick_count, dtype=int)
            ax3.set_xticks(tick_idx + 0.5)
            ax3.set_xticklabels([heatmap_dates[i].strftime("%Y-%m-%d") for i in tick_idx], rotation=0, fontsize=9)
            ax3.set_yticks(np.arange(rows) + 0.5)
            ax3.set_yticklabels(heatmap_data.index.tolist())
            ax3.set_xticks(np.arange(cols + 1), minor=True)
            ax3.set_yticks(np.arange(rows + 1), minor=True)
            ax3.grid(which="minor", color="black", linewidth=0.35, alpha=0.45)
            ax3.tick_params(which="minor", bottom=False, left=False)

            cbar = fig3.colorbar(sc, ax=ax3, label="Signed Exposure")
            cbar.ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.0f}"))
            fig3.tight_layout()
            if self.output_small_charts:
                fig3.savefig(self._out_path("holding_heatmap.png"), dpi=150)
            plt.close(fig3)

        # Liability timeline by ETF (for plotting only, no extra CSV output).
        short_by_ticker = (
            holding.loc[holding["direction"] == "short"]
            .pivot_table(index="date", columns="ticker", values="market_value", aggfunc="sum", fill_value=0.0)
            .sort_index()
        )
        if not short_by_ticker.empty:
            short_by_ticker = -short_by_ticker.abs()

        # Per-ETF stacked bar chart: long on top, short below zero.
        long_by_ticker = (
            holding.loc[holding["direction"] == "long"]
            .pivot_table(index="date", columns="ticker", values="market_value", aggfunc="sum", fill_value=0.0)
            .sort_index()
        )
        short_by_ticker = (
            holding.loc[holding["direction"] == "short"]
            .pivot_table(index="date", columns="ticker", values="market_value", aggfunc="sum", fill_value=0.0)
            .sort_index()
        )
        all_dates = sorted(set(long_by_ticker.index.tolist()) | set(short_by_ticker.index.tolist()))
        if all_dates:
            long_by_ticker = long_by_ticker.reindex(all_dates, fill_value=0.0)
            short_by_ticker = short_by_ticker.reindex(all_dates, fill_value=0.0)
        if not long_by_ticker.empty or not short_by_ticker.empty:
            all_tickers = sorted(set(long_by_ticker.columns.tolist()) | set(short_by_ticker.columns.tolist()))
            if not all_tickers:
                return metrics
            if not long_by_ticker.empty:
                long_by_ticker = long_by_ticker.reindex(columns=all_tickers, fill_value=0.0)
            else:
                long_by_ticker = pd.DataFrame(0.0, index=short_by_ticker.index, columns=all_tickers)
            if not short_by_ticker.empty:
                short_by_ticker = short_by_ticker.reindex(columns=all_tickers, fill_value=0.0)
            else:
                short_by_ticker = pd.DataFrame(0.0, index=long_by_ticker.index, columns=all_tickers)

            # Keep chart readable: top contributors + OTHER.
            mean_abs = (long_by_ticker.abs().mean() + short_by_ticker.abs().mean()).sort_values(ascending=False)
            top_tickers = mean_abs.index.tolist()[:8]
            other_tickers = [t for t in all_tickers if t not in top_tickers]
            display_tickers = top_tickers + (["OTHER"] if other_tickers else [])

            long_display = long_by_ticker.loc[:, top_tickers].copy()
            short_display = short_by_ticker.loc[:, top_tickers].copy()
            if other_tickers:
                long_display["OTHER"] = long_by_ticker.loc[:, other_tickers].sum(axis=1)
                short_display["OTHER"] = short_by_ticker.loc[:, other_tickers].sum(axis=1)

            color_map = plt.get_cmap(self.etf_cmap)
            color_by_ticker = {ticker: color_map(i % 20) for i, ticker in enumerate(display_tickers)}

            fig4, ax4 = plt.subplots(figsize=(14, 6))
            bar_width = 4.0
            long_bottom = np.zeros(len(long_display.index))
            short_bottom = np.zeros(len(short_display.index))
            for ticker in display_tickers:
                long_values = long_display[ticker].astype(float).to_numpy()
                short_values = -short_display[ticker].astype(float).abs().to_numpy()
                ax4.bar(
                    long_display.index,
                    long_values,
                    bottom=long_bottom,
                    width=bar_width,
                    color=color_by_ticker[ticker],
                    alpha=0.88,
                )
                ax4.bar(
                    short_display.index,
                    short_values,
                    bottom=short_bottom,
                    width=bar_width,
                    color=color_by_ticker[ticker],
                    alpha=0.88,
                )
                long_bottom += long_values
                short_bottom += short_values

            legend_handles = [Patch(facecolor=color_by_ticker[t], label=t, alpha=0.88) for t in display_tickers]
            ax4.axhline(0.0, color="black", linewidth=0.8, alpha=0.8)
            ax4.set_title("Per-ETF Stacked Bars (Long Above / Short Below)")
            ax4.set_xlabel("Date")
            ax4.set_ylabel("Exposure")
            ax4.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.0f}"))
            ax4.grid(color="black", linewidth=0.4, alpha=0.25, axis="y")
            self._style_date_axis(ax4)
            ax4.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8, title="ETF")

            fig4.tight_layout()
            if self.output_small_charts:
                fig4.savefig(self._out_path("holding_stacked.png"), dpi=150)
            plt.close(fig4)

        # High-resolution all-in-one dashboard panel.
        fig_panel, axes_panel = plt.subplots(9, 1, figsize=(24, 54))

        # 1) Total value
        axes_panel[0].plot(value_history["date"], equity, color="#1f77b4", linewidth=2)
        axes_panel[0].set_title("Total Value")
        axes_panel[0].set_ylabel("Total Value")
        axes_panel[0].yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.0f}"))
        axes_panel[0].grid(color="black", linewidth=0.4, alpha=0.25)
        self._style_date_axis(axes_panel[0])

        # 2) Drawdown
        axes_panel[1].fill_between(value_history["date"], drawdown, 0.0, color="#d62728", alpha=0.28)
        axes_panel[1].set_title("Drawdown")
        axes_panel[1].set_ylabel("Drawdown")
        axes_panel[1].yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y * 100:.1f}%"))
        axes_panel[1].grid(color="black", linewidth=0.4, alpha=0.25)
        self._style_date_axis(axes_panel[1])

        # 3) Net exposure
        if net_exposure_series is not None:
            axes_panel[2].plot(net_exposure_series["date"], net_exposure_series["signed_market_value"], color="#9467bd", linewidth=2)
            axes_panel[2].axhline(0.0, color="black", linewidth=0.8, alpha=0.8)
            axes_panel[2].set_title("Net Exposure")
            axes_panel[2].set_ylabel("Exposure")
            axes_panel[2].yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.0f}"))
            axes_panel[2].grid(color="black", linewidth=0.4, alpha=0.25)
            self._style_date_axis(axes_panel[2])
        else:
            axes_panel[2].set_title("Net Exposure (No Data)")
            axes_panel[2].axis("off")

        # 4) Asset/liability component trajectories
        axes_panel[3].plot(dates, cash_values, color="#7f7f7f", linewidth=1.8, label="Cash")
        axes_panel[3].plot(dates, security_values, color="#2ca02c", linewidth=1.8, label="Securities")
        axes_panel[3].plot(dates, liability_values, color="#d62728", linewidth=1.8, label="Liability (negative)")
        axes_panel[3].axhline(0.0, color="black", linewidth=0.8, alpha=0.8)
        axes_panel[3].set_title("Asset / Liability Components")
        axes_panel[3].set_ylabel("Value")
        axes_panel[3].yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.0f}"))
        axes_panel[3].grid(color="black", linewidth=0.4, alpha=0.25)
        axes_panel[3].legend(loc="upper left")
        self._style_date_axis(axes_panel[3])

        # 5) Total value trajectory
        axes_panel[4].plot(dates, value_components["total_value"], color="#1f77b4", linewidth=2.1)
        axes_panel[4].set_title("Total Value Trajectory")
        axes_panel[4].set_ylabel("Total Value")
        axes_panel[4].yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.0f}"))
        axes_panel[4].grid(color="black", linewidth=0.4, alpha=0.25)
        self._style_date_axis(axes_panel[4])

        # 6) Cumulative fee amount
        if "long_fee_cum" in value_history.columns and "short_fee_cum" in value_history.columns:
            axes_panel[5].plot(value_history["date"], value_history["long_fee_cum"].astype(float), color="#2ca02c", linewidth=1.9, label="Long")
            axes_panel[5].plot(value_history["date"], value_history["short_fee_cum"].astype(float), color="#d62728", linewidth=1.9, label="Short")
            axes_panel[5].set_title("Cumulative Trading Fee Amount")
            axes_panel[5].set_ylabel("Amount")
            axes_panel[5].yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.2f}"))
            axes_panel[5].grid(color="black", linewidth=0.4, alpha=0.25)
            axes_panel[5].legend(loc="upper left")
            self._style_date_axis(axes_panel[5])
        else:
            axes_panel[5].set_title("Cumulative Trading Fee Amount (No Data)")
            axes_panel[5].axis("off")

        # 7) Cumulative fee rate
        if "long_fee_rate_cum" in value_history.columns and "short_fee_rate_cum" in value_history.columns:
            axes_panel[6].plot(value_history["date"], value_history["long_fee_rate_cum"].astype(float), color="#2ca02c", linewidth=1.9, label="Long")
            axes_panel[6].plot(value_history["date"], value_history["short_fee_rate_cum"].astype(float), color="#d62728", linewidth=1.9, label="Short")
            axes_panel[6].set_title("Cumulative Trading Fee Rate")
            axes_panel[6].set_ylabel("Fee Rate")
            axes_panel[6].yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y * 100:.2f}%"))
            axes_panel[6].grid(color="black", linewidth=0.4, alpha=0.25)
            axes_panel[6].legend(loc="upper left")
            self._style_date_axis(axes_panel[6])
        else:
            axes_panel[6].set_title("Cumulative Trading Fee Rate (No Data)")
            axes_panel[6].axis("off")

        # 8) Heatmap
        if holding is not None:
            panel_heatmap = holding.pivot_table(
                index="ticker",
                columns="date",
                values="signed_market_value",
                aggfunc="sum",
                fill_value=0.0,
            )
            if not panel_heatmap.empty:
                ax_hm = axes_panel[7]
                ax_hm.set_facecolor("white")
                ax_hm.set_title("Holding Exposure Heatmap (Ticker x Date)")
                ax_hm.set_xlabel("Date")
                ax_hm.set_ylabel("Ticker")
                rows, cols = panel_heatmap.shape
                hm_values = panel_heatmap.to_numpy(dtype=float)
                hm_vmax = float(np.max(np.abs(hm_values)))
                if hm_vmax < 1e-12:
                    hm_vmax = 1.0
                x_centers = np.arange(cols) + 0.5
                y_centers = np.arange(rows) + 0.5
                xx, yy = np.meshgrid(x_centers, y_centers)
                flat_values = hm_values.reshape(-1)
                non_zero_mask = np.abs(flat_values) > 1e-12
                sc_hm = ax_hm.scatter(
                    xx.reshape(-1)[non_zero_mask],
                    yy.reshape(-1)[non_zero_mask],
                    c=flat_values[non_zero_mask],
                    cmap=self.heatmap_cmap,
                    vmin=-hm_vmax,
                    vmax=hm_vmax,
                    s=95.0,
                    marker="s",
                    linewidths=0.0,
                )
                ax_hm.set_xlim(0, cols)
                ax_hm.set_ylim(rows, 0)
                hm_dates = pd.to_datetime(panel_heatmap.columns)
                tick_count = min(10, cols)
                tick_idx = np.linspace(0, cols - 1, num=tick_count, dtype=int)
                ax_hm.set_xticks(tick_idx + 0.5)
                ax_hm.set_xticklabels([hm_dates[i].strftime("%Y-%m-%d") for i in tick_idx], rotation=0, fontsize=9)
                ax_hm.set_yticks(np.arange(rows) + 0.5)
                ax_hm.set_yticklabels(panel_heatmap.index.tolist())
                ax_hm.set_xticks(np.arange(cols + 1), minor=True)
                ax_hm.set_yticks(np.arange(rows + 1), minor=True)
                ax_hm.grid(which="minor", color="black", linewidth=0.35, alpha=0.45)
                ax_hm.tick_params(which="minor", bottom=False, left=False)
                fig_panel.colorbar(sc_hm, ax=ax_hm, label="Signed Exposure")
            else:
                axes_panel[7].set_title("Holding Exposure Heatmap (No Data)")
                axes_panel[7].axis("off")
        else:
            axes_panel[7].set_title("Holding Exposure Heatmap (No Data)")
            axes_panel[7].axis("off")

        # 9) Per-ETF stacked bars
        if holding is not None:
            panel_long = (
                holding.loc[holding["direction"] == "long"]
                .pivot_table(index="date", columns="ticker", values="market_value", aggfunc="sum", fill_value=0.0)
                .sort_index()
            )
            panel_short = (
                holding.loc[holding["direction"] == "short"]
                .pivot_table(index="date", columns="ticker", values="market_value", aggfunc="sum", fill_value=0.0)
                .sort_index()
            )
            all_dates_panel = sorted(set(panel_long.index.tolist()) | set(panel_short.index.tolist()))
            if all_dates_panel:
                panel_long = panel_long.reindex(all_dates_panel, fill_value=0.0)
                panel_short = panel_short.reindex(all_dates_panel, fill_value=0.0)
            all_tickers_panel = sorted(set(panel_long.columns.tolist()) | set(panel_short.columns.tolist()))
            if all_tickers_panel:
                panel_long = panel_long.reindex(columns=all_tickers_panel, fill_value=0.0)
                panel_short = panel_short.reindex(columns=all_tickers_panel, fill_value=0.0)
                mean_abs = (panel_long.abs().mean() + panel_short.abs().mean()).sort_values(ascending=False)
                top_tickers = mean_abs.index.tolist()[:8]
                other_tickers = [t for t in all_tickers_panel if t not in top_tickers]
                display_tickers = top_tickers + (["OTHER"] if other_tickers else [])
                panel_long_display = panel_long.loc[:, top_tickers].copy()
                panel_short_display = panel_short.loc[:, top_tickers].copy()
                if other_tickers:
                    panel_long_display["OTHER"] = panel_long.loc[:, other_tickers].sum(axis=1)
                    panel_short_display["OTHER"] = panel_short.loc[:, other_tickers].sum(axis=1)
                ax_stk = axes_panel[8]
                color_map = plt.get_cmap(self.etf_cmap)
                color_by_ticker = {ticker: color_map(i % 20) for i, ticker in enumerate(display_tickers)}
                bar_width = 4.0
                long_bottom = np.zeros(len(panel_long_display.index))
                short_bottom = np.zeros(len(panel_short_display.index))
                for ticker in display_tickers:
                    long_values = panel_long_display[ticker].astype(float).to_numpy()
                    short_values = -panel_short_display[ticker].astype(float).abs().to_numpy()
                    ax_stk.bar(panel_long_display.index, long_values, bottom=long_bottom, width=bar_width, color=color_by_ticker[ticker], alpha=0.88)
                    ax_stk.bar(panel_short_display.index, short_values, bottom=short_bottom, width=bar_width, color=color_by_ticker[ticker], alpha=0.88)
                    long_bottom += long_values
                    short_bottom += short_values
                legend_handles = [Patch(facecolor=color_by_ticker[t], label=t, alpha=0.88) for t in display_tickers]
                ax_stk.axhline(0.0, color="black", linewidth=0.8, alpha=0.8)
                ax_stk.set_title("Per-ETF Stacked Bars (Long Above / Short Below)")
                ax_stk.set_xlabel("Date")
                ax_stk.set_ylabel("Exposure")
                ax_stk.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.0f}"))
                ax_stk.grid(color="black", linewidth=0.4, alpha=0.25, axis="y")
                self._style_date_axis(ax_stk)
                ax_stk.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8, title="ETF")
            else:
                axes_panel[8].set_title("Per-ETF Stacked Bars (No Data)")
                axes_panel[8].axis("off")
        else:
            axes_panel[8].set_title("Per-ETF Stacked Bars (No Data)")
            axes_panel[8].axis("off")

        fig_panel.tight_layout()
        fig_panel.savefig(self._out_path("all_in_one_panel.png"), dpi=300)
        plt.close(fig_panel)

        return metrics
