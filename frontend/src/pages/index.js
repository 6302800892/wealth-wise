import CustomerDetailPage from "./advisor/CustomerDetailPage.jsx";
import CustomersPage from "./advisor/CustomersPage.jsx";
import AssetClassesPage from "./admin/AssetClassesPage.jsx";
import NavPage from "./admin/NavPage.jsx";
import RuleSetsPage from "./admin/RuleSetsPage.jsx";
import TemplatesPage from "./admin/TemplatesPage.jsx";
import DashboardPage from "./customer/DashboardPage.jsx";
import GoalsPage from "./customer/GoalsPage.jsx";
import HoldingsPage from "./customer/HoldingsPage.jsx";
import RebalancingPage from "./customer/RebalancingPage.jsx";
import RecommendationPage from "./customer/RecommendationPage.jsx";
import RiskProfilePage from "./customer/RiskProfilePage.jsx";

// Route name → page component (see config/routes.js).
export const PAGES = {
  dashboard: DashboardPage,
  "risk-profile": RiskProfilePage,
  goals: GoalsPage,
  recommendation: RecommendationPage,
  holdings: HoldingsPage,
  rebalancing: RebalancingPage,
  "advisor-customers": CustomersPage,
  "advisor-customer": CustomerDetailPage,
  "admin-templates": TemplatesPage,
  "admin-rule-sets": RuleSetsPage,
  "admin-asset-classes": AssetClassesPage,
  "admin-nav": NavPage,
};
