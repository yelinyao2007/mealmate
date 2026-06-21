import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { useLanguage } from '../context/LanguageContext';
import { Play, CheckCircle, XCircle, Clock, Loader2, ChevronRight, Zap, Users, ShoppingCart, Utensils } from 'lucide-react';

const WORKFLOW_ICONS = {
  full_meal_service: Zap,
  menu_and_nutrition: Utensils,
  menu_and_procurement: ShoppingCart,
  custom_meal_plan: Users,
};

const SEASONS = ['春季', '夏季', '秋季', '冬季'];

export default function WorkflowDashboard() {
  const { t } = useLanguage();
  const [workflowTypes, setWorkflowTypes] = useState({});
  const [history, setHistory] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState('full_meal_service');
  const [executing, setExecuting] = useState(false);
  const [currentResult, setCurrentResult] = useState(null);
  const [activeTab, setActiveTab] = useState('config'); // config | result | history

  // Config form state
  const [config, setConfig] = useState({
    budget_per_meal: 15,
    num_people: 100,
    season: '春季',
    dietary_requirements: [],
    special_requirements: '',
    target_groups: ['青年白领'], // 默认青年白领群体
    health_conditions: [],
  });

  useEffect(() => {
    loadWorkflowTypes();
    loadHistory();
  }, []);

  const loadWorkflowTypes = async () => {
    try {
      const res = await api.get('/workflow/types');
      setWorkflowTypes(res.data);
    } catch (err) {
      console.error('Failed to load workflow types', err);
    }
  };

  const loadHistory = async () => {
    try {
      const res = await api.get('/workflow/history');
      setHistory(res.data);
    } catch (err) {
      console.error('Failed to load history', err);
    }
  };

  const executeWorkflow = async () => {
    console.log('executeWorkflow called');
    console.log('Current config:', config);
    console.log('Selected workflow:', selectedWorkflow);
    setExecuting(true);
    setCurrentResult(null);
    setActiveTab('result');
    try {
      const res = await api.post('/workflow/execute', {
        workflow_type: selectedWorkflow,
        ...config,
      });
      console.log('Workflow execution response:', res.data);
      
      // Adapt the response format to match what the UI expects
      const adaptedResult = {
        status: res.data.status === 'completed' ? 'success' : 'error',
        result_data: res.data.result_data || res.data.result,
        steps_log: res.data.steps_log || [],
        total_duration_ms: res.data.total_duration_ms || 0,
        error_message: res.data.error_message,
      };
      
      setCurrentResult(adaptedResult);
      loadHistory();
    } catch (err) {
      console.error('Workflow execution error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Workflow execution failed';
      console.error('Error message:', errorMessage);
      setCurrentResult({ error_message: errorMessage, status: 'error' });
    } finally {
      setExecuting(false);
    }
  };

  const loadExecution = async (id) => {
    try {
      const res = await api.get(`/workflow/${id}`);
      const adaptedResult = {
        status: res.data.status === 'completed' ? 'success' : 'error',
        result_data: res.data.output_data || res.data.result_data || {},
        steps_log: res.data.steps_log || [],
        total_duration_ms: res.data.total_duration_ms || 0,
        error_message: res.data.error_message,
      };
      setCurrentResult(adaptedResult);
      setActiveTab('result');
    } catch (err) {
      console.error('Failed to load execution', err);
    }
  };

  const DIETARY_OPTIONS = ['素食', '清真', '低盐', '低糖', '低脂', '高蛋白', '无辣'];
  const HEALTH_OPTIONS = ['增肌减脂', '素食主义', '低碳水', '增重', '过敏体质'];
  const TARGET_GROUPS = ['青年白领', '健身爱好者', '素食主义者', '加班族', '学生党', '美食博主', '新手厨师', '家庭煮夫'];

  return (
    <div className="web-container web-section">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="font-heading text-4xl flex items-center justify-center gap-2">
          <Zap className="text-terracotta" size={32} />
          {t('workflow.title')}
        </h1>
        <p className="text-charcoal/60 mt-1">{t('workflow.subtitle')}</p>
      </div>

      {/* Workflow Type Selector */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {Object.entries(workflowTypes).map(([key, wf]) => {
          const Icon = WORKFLOW_ICONS[key] || Zap;
          return (
            <button
              key={key}
              onClick={() => setSelectedWorkflow(key)}
              className={`card text-left border-2 transition-colors ${
                selectedWorkflow === key ? 'border-terracotta bg-terracotta/5' : 'border-transparent'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Icon size={18} className="text-terracotta" />
                <h3 className="font-heading text-base">{wf.name}</h3>
              </div>
              <p className="text-xs text-charcoal/50">{wf.description}</p>
              <div className="mt-2 flex gap-1 flex-wrap">
                {wf.agents?.map((a, i) => (
                  <span key={i} className="chip text-xs py-0.5 px-2">{a.replace('Agent', '')}</span>
                ))}
              </div>
            </button>
          );
        })}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b-2 border-gold/20 mb-6">
        {[
          { id: 'config', label: t('workflow.tabConfig') },
          { id: 'result', label: t('workflow.tabResult') },
          { id: 'history', label: t('workflow.tabHistory') },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 font-medium text-sm border-b-2 -mb-[2px] transition-colors ${
              activeTab === tab.id
                ? 'border-terracotta text-terracotta'
                : 'border-transparent text-charcoal/50 hover:text-charcoal'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Config Panel */}
      {activeTab === 'config' && (
        <div className="card">
          <h2 className="font-heading text-xl mb-4">{t('workflow.configTitle')}</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">{t('workflow.budgetPerMeal')}</label>
              <input
                type="number"
                value={config.budget_per_meal}
                onChange={(e) => setConfig({ ...config, budget_per_meal: Number(e.target.value) })}
                className="input-field"
                min="5"
                max="100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t('workflow.numPeople')}</label>
              <input
                type="number"
                value={config.num_people}
                onChange={(e) => setConfig({ ...config, num_people: Number(e.target.value) })}
                className="input-field"
                min="10"
                max="1000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t('workflow.season')}</label>
              <select
                value={config.season}
                onChange={(e) => setConfig({ ...config, season: e.target.value })}
                className="input-field"
              >
                {SEASONS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t('workflow.specialReq')}</label>
              <input
                type="text"
                value={config.special_requirements}
                onChange={(e) => setConfig({ ...config, special_requirements: e.target.value })}
                className="input-field"
                placeholder={t('workflow.specialReqPlaceholder')}
              />
            </div>
          </div>

          {/* Dietary Requirements */}
          <div className="mt-4">
            <label className="block text-sm font-medium mb-2">{t('workflow.dietaryReq')}</label>
            <div className="flex flex-wrap gap-2">
              {DIETARY_OPTIONS.map((opt) => (
                <button
                  key={opt}
                  onClick={() => {
                    const arr = config.dietary_requirements.includes(opt)
                      ? config.dietary_requirements.filter((d) => d !== opt)
                      : [...config.dietary_requirements, opt];
                    setConfig({ ...config, dietary_requirements: arr });
                  }}
                  className={`chip cursor-pointer transition-colors ${
                    config.dietary_requirements.includes(opt) ? 'bg-terracotta/20 text-terracotta' : ''
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>

          {/* Target Groups (for custom_meal_plan / full_meal_service) */}
          {(selectedWorkflow === 'full_meal_service' || selectedWorkflow === 'custom_meal_plan') && (
            <>
              <div className="mt-4">
                <label className="block text-sm font-medium mb-2">{t('workflow.targetGroups')}</label>
                <div className="flex flex-wrap gap-2">
                  {TARGET_GROUPS.map((g) => (
                    <button
                      key={g}
                      onClick={() => {
                        const arr = config.target_groups.includes(g)
                          ? config.target_groups.filter((x) => x !== g)
                          : [...config.target_groups, g];
                        setConfig({ ...config, target_groups: arr });
                      }}
                      className={`chip cursor-pointer transition-colors ${
                        config.target_groups.includes(g) ? 'bg-sage/30 text-sage' : ''
                      }`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium mb-2">{t('workflow.healthConditions')}</label>
                <div className="flex flex-wrap gap-2">
                  {HEALTH_OPTIONS.map((h) => (
                    <button
                      key={h}
                      onClick={() => {
                        const arr = config.health_conditions.includes(h)
                          ? config.health_conditions.filter((x) => x !== h)
                          : [...config.health_conditions, h];
                        setConfig({ ...config, health_conditions: arr });
                      }}
                      className={`chip cursor-pointer transition-colors ${
                        config.health_conditions.includes(h) ? 'bg-gold/40 text-charcoal' : ''
                      }`}
                    >
                      {h}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Execute Button */}
          <button
            onClick={() => {
              console.log('Button clicked!');
              console.log('Current config:', config);
              console.log('Selected workflow:', selectedWorkflow);
              executeWorkflow();
            }}
            disabled={executing}
            className="btn-primary mt-6 flex items-center gap-2 w-full justify-center text-lg py-3"
          >
            {executing ? (
              <><Loader2 size={20} className="animate-spin" /> {t('workflow.executing')}</>
            ) : (
              <><Play size={20} /> {t('workflow.execute')}</>
            )}
          </button>
        </div>
      )}

      {/* Result Panel */}
      {activeTab === 'result' && (
        <div>
          {executing && (
            <div className="card text-center py-12">
              <Loader2 size={48} className="animate-spin text-terracotta mx-auto mb-4" />
              <p className="font-heading text-xl">{t('workflow.agentsWorking')}</p>
              <p className="text-charcoal/50 mt-1">{t('workflow.pleaseWait')}</p>
            </div>
          )}
          {!executing && currentResult && (
            <WorkflowResultView result={currentResult} t={t} />
          )}
          {!executing && !currentResult && (
            <div className="card text-center py-12 text-charcoal/40">
              <Zap size={48} className="mx-auto mb-3 opacity-30" />
              <p>{t('workflow.noResult')}</p>
            </div>
          )}
        </div>
      )}

      {/* History Panel */}
      {activeTab === 'history' && (
        <div className="space-y-3">
          {history.length === 0 && (
            <div className="card text-center py-8 text-charcoal/40">
              <p>{t('workflow.noHistory')}</p>
            </div>
          )}
          {history.map((exec) => (
            <button
              key={exec.id}
              onClick={() => loadExecution(exec.id)}
              className="card w-full text-left flex items-center justify-between hover:shadow-lg transition-shadow"
            >
              <div>
                <div className="flex items-center gap-2">
                  {exec.status === 'completed' ? (
                    <CheckCircle size={16} className="text-sage" />
                  ) : (
                    <XCircle size={16} className="text-red-400" />
                  )}
                  <span className="font-medium">{workflowTypes[exec.workflow_type]?.name || exec.workflow_type}</span>
                </div>
                <div className="flex items-center gap-3 mt-1 text-xs text-charcoal/50">
                  <span className="flex items-center gap-1">
                    <Clock size={12} /> {(exec.total_duration_ms / 1000).toFixed(1)}s
                  </span>
                  <span>{exec.steps_count} {t('workflow.steps')}</span>
                  <span>{new Date(exec.created_at).toLocaleString()}</span>
                </div>
              </div>
              <ChevronRight size={16} className="text-charcoal/30" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function WorkflowResultView({ result, t }) {
  const [expandedSection, setExpandedSection] = useState('menu_plan');

  if (result.status === 'error') {
    return (
      <div className="card border-2 border-red-200 bg-red-50/50">
        <div className="flex items-center gap-2 text-red-600 mb-2">
          <XCircle size={20} />
          <h3 className="font-heading text-lg">{t('workflow.error')}</h3>
        </div>
        <p className="text-sm text-red-500">{result.error_message}</p>
      </div>
    );
  }

  const data = result.result_data || {};
  const steps = result.steps_log || [];

  const SECTION_CONFIG = {
    menu_plan: { title: t('workflow.menuPlan'), icon: '📋' },
    nutrition_analysis: { title: t('workflow.nutritionAnalysis'), icon: '🥗' },
    procurement: { title: t('workflow.procurement'), icon: '🛒' },
    meal_customization: { title: t('workflow.mealCustomization'), icon: '👴' },
  };

  return (
    <div className="space-y-4">
      {/* Execution Steps Timeline */}
      <div className="card">
        <h3 className="font-heading text-lg mb-3 flex items-center gap-2">
          <CheckCircle size={18} className="text-sage" />
          {t('workflow.executionSteps')}
          <span className="text-sm text-charcoal/50 font-normal ml-auto">
            {t('workflow.totalTime')}: {(result.total_duration_ms / 1000).toFixed(1)}s
          </span>
        </h3>
        <div className="space-y-2">
          {steps.map((step, i) => (
            <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-cream">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold ${
                step.status === 'completed' ? 'bg-sage' : 'bg-red-400'
              }`}>
                {step.step_number}
              </div>
              <div className="flex-1">
                <span className="font-medium text-sm">{step.agent_name}</span>
                {step.error && <span className="text-xs text-red-400 ml-2">{step.error}</span>}
              </div>
              <span className="text-xs text-charcoal/50">{(step.duration_ms / 1000).toFixed(1)}s</span>
            </div>
          ))}
        </div>
      </div>

      {/* Result Sections */}
      {Object.entries(SECTION_CONFIG).map(([key, cfg]) => {
        if (!data[key]) return null;
        return (
          <div key={key} className="card">
            <button
              onClick={() => setExpandedSection(expandedSection === key ? '' : key)}
              className="w-full flex items-center justify-between"
            >
              <h3 className="font-heading text-lg flex items-center gap-2">
                <span>{cfg.icon}</span> {cfg.title}
              </h3>
              <ChevronRight size={18} className={`transform transition-transform ${expandedSection === key ? 'rotate-90' : ''}`} />
            </button>
            {expandedSection === key && (
              <div className="mt-4">
                <ResultDataRenderer data={data[key]} sectionKey={key} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function ResultDataRenderer({ data, sectionKey }) {
  if (!data) return null;

  // Unwrap raw_response if the LLM JSON parsing failed on the server side
  if (data.raw_response && typeof data.raw_response === 'string') {
    try {
      const parsed = JSON.parse(data.raw_response);
      data = parsed;
    } catch (e) {
      // Keep original data if parsing fails
    }
  }

  // Menu Plan renderer
  if (sectionKey === 'menu_plan' && data.weekly_menu) {
    return (
      <div className="space-y-4">
        {data.nutrition_summary && (
          <p className="text-sm text-charcoal/70 bg-sage/10 p-3 rounded-lg">{data.nutrition_summary}</p>
        )}
        {Object.entries(data.weekly_menu).map(([day, meals]) => (
          <div key={day} className="border rounded-xl p-3">
            <h4 className="font-heading text-base text-terracotta mb-2">{day}</h4>
            {typeof meals === 'object' && Object.entries(meals).map(([mealType, mealData]) => (
              <div key={mealType} className="ml-2 mb-2">
                <span className="font-medium text-sm">{mealType}：</span>
                {typeof mealData === 'object' ? (
                  <div className="ml-2 text-sm text-charcoal/70">
                    {Object.entries(mealData).map(([k, v]) => (
                      <div key={k}>
                        <span className="font-medium">{k}：</span>
                        {Array.isArray(v) ? v.join('、') : String(v)}
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="text-sm text-charcoal/70">{String(mealData)}</span>
                )}
              </div>
            ))}
          </div>
        ))}
        {data.total_weekly_cost_per_person && (
          <p className="text-sm font-medium">
            每人每周总费用：¥{data.total_weekly_cost_per_person}
          </p>
        )}
      </div>
    );
  }

  // Nutrition Analysis renderer
  if (sectionKey === 'nutrition_analysis') {
    return (
      <div className="space-y-4">
        {data.overall_score != null && (
          <div className="flex items-center gap-3 bg-sage/10 p-4 rounded-xl">
            <div className={`text-3xl font-bold ${data.overall_score >= 80 ? 'text-sage' : data.overall_score >= 60 ? 'text-gold' : 'text-red-400'}`}>
              {data.overall_score}
            </div>
            <div>
              <div className="font-medium">综合营养评分</div>
              {data.elderly_friendly_score != null && (
                <div className="text-sm text-charcoal/50">适老评分：{data.elderly_friendly_score}</div>
              )}
            </div>
          </div>
        )}
        {data.weekly_summary && (
          <div className="space-y-2 text-sm">
            {data.weekly_summary.strengths && (
              <div><span className="font-medium text-sage">优点：</span>{data.weekly_summary.strengths.join('、')}</div>
            )}
            {data.weekly_summary.weaknesses && (
              <div><span className="font-medium text-red-400">不足：</span>{data.weekly_summary.weaknesses.join('、')}</div>
            )}
            {data.weekly_summary.improvement_suggestions && (
              <div>
                <span className="font-medium text-terracotta">改进建议：</span>
                <ul className="list-disc ml-5 mt-1">
                  {data.weekly_summary.improvement_suggestions.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            )}
          </div>
        )}
        {data.elderly_notes && (
          <p className="text-sm text-charcoal/70 bg-gold/10 p-3 rounded-lg">
            <span className="font-medium">适老化建议：</span>{data.elderly_notes}
          </p>
        )}
      </div>
    );
  }

  // Procurement renderer
  if (sectionKey === 'procurement') {
    const list = data.procurement_list || data;
    const totalBudget = data.total_budget || data.total_budget_per_person_per_day;
    if (!list || (typeof list === 'object' && Object.keys(list).length === 0)) return null;
    return (
      <div className="space-y-4">
        {totalBudget && (
          <div className="bg-terracotta/10 p-4 rounded-xl flex items-center justify-between">
            <span className="font-medium">总预算</span>
            <span className="text-xl font-bold text-terracotta">¥{totalBudget}</span>
          </div>
        )}
        {data.storage_notes && (
          <p className="text-sm text-charcoal/70 bg-gold/10 p-3 rounded-lg">{data.storage_notes}</p>
        )}
        {Array.isArray(list) ? (
          <div className="space-y-2">
            {list.map((item, i) => (
              <div key={i} className="flex items-center justify-between p-2 bg-cream rounded-lg">
                <span className="text-sm">{item.name || item.ingredient}</span>
                <span className="text-sm font-medium">{item.quantity}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {Object.entries(list).map(([category, items]) => (
              <div key={category}>
                <h4 className="font-heading text-sm text-terracotta mb-2">{category}</h4>
                {Array.isArray(items) && items.length > 0 ? (
                  <div className="space-y-1">
                    {items.map((item, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-cream rounded-lg">
                        <span className="text-sm">{item.name || item.ingredient}</span>
                        <span className="text-sm font-medium">{item.quantity}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center justify-between p-2 bg-cream rounded-lg">
                    <span className="text-sm">{items}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        {data.waste_reduction_tips && (
          <div className="bg-sage/10 p-3 rounded-lg">
            <h4 className="font-medium text-sm mb-1">减少浪费建议</h4>
            <ul className="text-sm text-charcoal/70 list-disc ml-4">
              {data.waste_reduction_tips.map((tip, i) => <li key={i}>{tip}</li>)}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // Meal Customization renderer
  if (sectionKey === 'meal_customization') {
    const plans = data.customized_plans || data.customization_plans;
    const notes = data.customization_notes || data.general_notes || data.delivery_suggestions;
    if (!plans && !notes) return null;
    return (
      <div className="space-y-4">
        {notes && (
          <div className="bg-gold/10 p-4 rounded-xl">
            <h4 className="font-medium mb-2">定制说明</h4>
            <p className="text-sm text-charcoal/70">{typeof notes === 'string' ? notes : JSON.stringify(notes)}</p>
          </div>
        )}
        {plans && Array.isArray(plans) && plans.map((plan, i) => (
          <div key={i} className="border rounded-xl p-3">
            <h4 className="font-heading text-base text-terracotta mb-2">{plan.target_group || plan.target || `方案${i + 1}`}</h4>
            {plan.modifications && (
              <p className="text-sm text-charcoal/70 mb-2">{plan.modifications}</p>
            )}
            {plan.nutrition_notes && (
              <p className="text-sm text-sage mb-2">营养提示：{plan.nutrition_notes}</p>
            )}
            {plan.preparation_tips && (
              <p className="text-sm text-gold mb-2">备餐建议：{plan.preparation_tips}</p>
            )}
            {plan.daily_plans && Object.entries(plan.daily_plans).map(([day, meals]) => (
              <div key={day} className="ml-2 mb-2">
                <span className="font-medium text-sm">{day}：</span>
                {typeof meals === 'object' ? (
                  <div className="ml-2 text-sm text-charcoal/70">
                    {Object.entries(meals).map(([mealType, mealData]) => (
                      <div key={mealType}>
                        <span className="font-medium">{mealType}：</span>
                        {typeof mealData === 'object' ? (
                          <div className="ml-2">{Object.entries(mealData).map(([k, v]) => (
                            <div key={k}>{k}：{Array.isArray(v) ? v.join('、') : String(v)}</div>
                          ))}</div>
                        ) : (
                          String(mealData)
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="text-sm text-charcoal/70">{String(meals)}</span>
                )}
              </div>
            ))}
            {plan.safety_reminders && (
              <div className="bg-red-50 p-2 rounded-lg mt-2">
                <span className="text-sm text-red-500 font-medium">安全提醒：</span>
                <ul className="text-sm text-red-400 list-disc ml-4">
                  {plan.safety_reminders.map((r, j) => <li key={j}>{r}</li>)}
                </ul>
              </div>
            )}
          </div>
        ))}
        {plans && !Array.isArray(plans) && (
          <div className="space-y-2">
            {Object.entries(plans).map(([group, details]) => (
              <div key={group} className="border rounded-xl p-3">
                <h4 className="font-heading text-base text-terracotta mb-2">{group}</h4>
                {typeof details === 'object' ? (
                  <div className="text-sm text-charcoal/70 space-y-1">
                    {Object.entries(details).map(([k, v]) => (
                      <div key={k}><span className="font-medium">{k}：</span>{String(v)}</div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-charcoal/70">{String(details)}</p>
                )}
              </div>
            ))}
          </div>
        )}
        {data.safety_reminders && (
          <div className="bg-red-50 p-3 rounded-lg">
            <h4 className="font-medium text-sm mb-1">安全提醒</h4>
            <ul className="text-sm text-red-400 list-disc ml-4">
              {data.safety_reminders.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        )}
      </div>
    );
  }

  return <p className="text-sm text-charcoal/50">No data available for this section</p>;
}