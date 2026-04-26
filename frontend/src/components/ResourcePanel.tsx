import { useState } from 'react';
import {
  ExternalLink,
  BookOpen,
  PlayCircle,
  FileText,
  Lightbulb,
  Search,
  GraduationCap,
  Wrench,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Globe,
} from 'lucide-react';
import type { ResourceRecommendations, StudyResource, TopicResources } from '../types';

interface ResourcePanelProps {
  resources: ResourceRecommendations;
  onRefresh?: () => void;
  refreshing?: boolean;
}

const RESOURCE_TYPE_CONFIG: Record<string, { icon: typeof BookOpen; label: string; bg: string; text: string }> = {
  video: { icon: PlayCircle, label: 'Video', bg: 'bg-red-100', text: 'text-red-700' },
  textbook: { icon: BookOpen, label: 'Textbook', bg: 'bg-blue-100', text: 'text-blue-700' },
  practice: { icon: FileText, label: 'Practice', bg: 'bg-orange-100', text: 'text-orange-700' },
  article: { icon: Globe, label: 'Article', bg: 'bg-green-100', text: 'text-green-700' },
  tool: { icon: Wrench, label: 'Tool', bg: 'bg-purple-100', text: 'text-purple-700' },
  course: { icon: GraduationCap, label: 'Course', bg: 'bg-teal-100', text: 'text-teal-700' },
};

const PRIORITY_BADGE: Record<string, string> = {
  high: 'bg-red-50 text-red-600 border-red-200',
  medium: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  low: 'bg-gray-50 text-gray-500 border-gray-200',
};

function ResourceTypeBadge({ type }: { type: string }) {
  const config = RESOURCE_TYPE_CONFIG[type] || RESOURCE_TYPE_CONFIG.article;
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
}

function ResourceCard({ resource }: { resource: StudyResource }) {
  const priorityStyle = PRIORITY_BADGE[resource.priority] || PRIORITY_BADGE.medium;
  const linkUrl = resource.url || `https://www.google.com/search?q=${encodeURIComponent(resource.title)}`;

  return (
    <a
      href={linkUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-3 bg-[#FFFBF1] border border-[#485C11]/15 rounded-lg hover:border-[#485C11]/40 hover:shadow-sm transition-all group"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <ResourceTypeBadge type={resource.resource_type} />
            <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border ${priorityStyle}`}>
              {resource.priority}
            </span>
          </div>
          <h4 className="font-medium text-sm text-[#485C11] group-hover:underline leading-snug">
            {resource.title}
          </h4>
          <p className="text-xs text-[#485C11]/50 mt-0.5">{resource.platform}</p>
          <p className="text-xs text-gray-500 mt-1 leading-relaxed">{resource.relevance}</p>
        </div>
        <ExternalLink className="w-4 h-4 text-[#485C11]/30 group-hover:text-[#485C11] transition-colors shrink-0 mt-1" />
      </div>
    </a>
  );
}

function TopicSection({ topic }: { topic: TopicResources }) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="border border-[#485C11]/15 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-[#F5EDD6] hover:bg-[#eee3c8] transition-colors"
      >
        <div className="flex items-center gap-2 text-left">
          <BookOpen className="w-4 h-4 text-[#485C11]" />
          <span className="font-semibold text-sm text-[#485C11]">{topic.topic}</span>
          <span className="text-xs text-[#485C11]/50">({topic.resources.length} resources)</span>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-[#485C11]/50" />
        ) : (
          <ChevronDown className="w-4 h-4 text-[#485C11]/50" />
        )}
      </button>
      {expanded && (
        <div className="p-3 space-y-2">
          {topic.related_events.length > 0 && (
            <p className="text-xs text-[#485C11]/60 mb-2">
              Related to: {topic.related_events.join(', ')}
            </p>
          )}
          {topic.resources.map((resource, i) => (
            <ResourceCard key={i} resource={resource} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ResourcePanel({ resources, onRefresh, refreshing }: ResourcePanelProps) {
  const [filter, setFilter] = useState<string>('all');

  const allResourceTypes = new Set<string>();
  resources.general_resources.forEach((r) => allResourceTypes.add(r.resource_type));
  resources.topic_resources.forEach((t) =>
    t.resources.forEach((r) => allResourceTypes.add(r.resource_type)),
  );

  const filterResources = (list: StudyResource[]) =>
    filter === 'all' ? list : list.filter((r) => r.resource_type === filter);

  const totalResources =
    resources.general_resources.length +
    resources.topic_resources.reduce((acc, t) => acc + t.resources.length, 0);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-[#485C11]" />
          <h3 className="font-semibold text-[#485C11]">
            AI-Curated Resources
          </h3>
          <span className="text-xs text-[#485C11]/50">
            {totalResources} resources found · {resources.subject_domain}
          </span>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium border border-[#485C11]/30 text-[#485C11] rounded-full hover:bg-[#d4ecd4] transition-colors disabled:opacity-50"
          >
            <Search className="w-3 h-3" />
            {refreshing ? 'Searching...' : 'Refresh'}
          </button>
        )}
      </div>

      {/* Filter chips */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
            filter === 'all'
              ? 'bg-[#485C11] text-white'
              : 'bg-[#F5EDD6] text-[#485C11] hover:bg-[#eee3c8]'
          }`}
        >
          All ({totalResources})
        </button>
        {Array.from(allResourceTypes).map((type) => {
          const config = RESOURCE_TYPE_CONFIG[type] || RESOURCE_TYPE_CONFIG.article;
          const count =
            resources.general_resources.filter((r) => r.resource_type === type).length +
            resources.topic_resources.reduce(
              (acc, t) => acc + t.resources.filter((r) => r.resource_type === type).length,
              0,
            );
          return (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                filter === type
                  ? 'bg-[#485C11] text-white'
                  : 'bg-[#F5EDD6] text-[#485C11] hover:bg-[#eee3c8]'
              }`}
            >
              {config.label} ({count})
            </button>
          );
        })}
      </div>

      {/* Study Tips */}
      {resources.study_tips.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="w-4 h-4 text-amber-600" />
            <span className="text-sm font-medium text-amber-800">Study Tips</span>
          </div>
          <ul className="space-y-1">
            {resources.study_tips.map((tip, i) => (
              <li key={i} className="text-xs text-amber-700 flex items-start gap-2">
                <span className="text-amber-400 mt-0.5">•</span>
                {tip}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* General Resources */}
      {filterResources(resources.general_resources).length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-[#485C11]/60 uppercase tracking-wider mb-2">
            General Course Resources
          </h4>
          <div className="space-y-2">
            {filterResources(resources.general_resources).map((resource, i) => (
              <ResourceCard key={i} resource={resource} />
            ))}
          </div>
        </div>
      )}

      {/* Topic Resources */}
      {resources.topic_resources.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-[#485C11]/60 uppercase tracking-wider">
            Resources by Topic
          </h4>
          {resources.topic_resources
            .filter((t) => filterResources(t.resources).length > 0)
            .map((topic, i) => (
              <TopicSection
                key={i}
                topic={
                  filter === 'all'
                    ? topic
                    : { ...topic, resources: filterResources(topic.resources) }
                }
              />
            ))}
        </div>
      )}

      {/* Empty state */}
      {totalResources === 0 && (
        <div className="text-center py-8">
          <Search className="w-8 h-8 text-[#485C11]/20 mx-auto mb-2" />
          <p className="text-sm text-[#485C11]/50">No resources found yet.</p>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="mt-2 text-sm text-[#485C11] underline hover:no-underline"
            >
              Search for resources
            </button>
          )}
        </div>
      )}
    </div>
  );
}
