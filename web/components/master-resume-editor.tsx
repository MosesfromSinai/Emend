"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FactList } from "@/components/fact-list";
import { StringList } from "@/components/string-list";
import { slugSectionId } from "@/lib/master-resume";
import type { Education, Experience, MasterResume, Project } from "@/lib/types";

type Props = {
  master: MasterResume;
  onChange: (master: MasterResume) => void;
};

function usedSectionIds(master: MasterResume): Set<string> {
  return new Set([...master.experiences, ...master.projects].map((s) => s.id));
}

export function MasterResumeEditor({ master, onChange }: Props) {
  const set = <K extends keyof MasterResume>(key: K, value: MasterResume[K]) =>
    onChange({ ...master, [key]: value });

  return (
    <div className="flex flex-col gap-8">
      <section className="grid grid-cols-2 gap-3">
        <Input
          value={master.name}
          onChange={(e) => set("name", e.target.value)}
          placeholder="Full name"
        />
        <Input
          value={master.email}
          onChange={(e) => set("email", e.target.value)}
          placeholder="Email"
        />
        <Input
          value={master.phone}
          onChange={(e) => set("phone", e.target.value)}
          placeholder="Phone"
        />
        <div className="col-span-2">
          <StringList
            items={master.links}
            onChange={(links) => set("links", links)}
            placeholder="linkedin.com/in/..."
            addLabel="Add link"
          />
        </div>
      </section>

      <ExperienceSection master={master} onChange={onChange} />
      <ProjectSection master={master} onChange={onChange} />
      <EducationSection master={master} onChange={onChange} />
      <SkillsSection master={master} onChange={onChange} />
    </div>
  );
}

function SectionHeading({ title, count }: { title: string; count: number }) {
  return (
    <div className="mb-3 flex items-baseline justify-between">
      <h2 className="font-serif text-xl font-semibold">{title}</h2>
      <span className="font-mono text-xs text-em-deep">
        {count} fact{count === 1 ? "" : "s"}
      </span>
    </div>
  );
}

function ExperienceSection({ master, onChange }: Props) {
  const update = (next: Experience[]) => onChange({ ...master, experiences: next });
  const factCount = master.experiences.reduce((n, e) => n + e.facts.length, 0);

  return (
    <section>
      <SectionHeading title="Experience" count={factCount} />
      <div className="flex flex-col gap-5">
        {master.experiences.map((exp, index) => (
          <div key={exp.id} className="rounded-lg border border-em-softb p-4">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <Input
                value={exp.company}
                onChange={(e) => {
                  const next = [...master.experiences];
                  next[index] = { ...exp, company: e.target.value };
                  update(next);
                }}
                placeholder="Company"
                className="w-auto flex-1"
              />
              <Input
                value={exp.title}
                onChange={(e) => {
                  const next = [...master.experiences];
                  next[index] = { ...exp, title: e.target.value };
                  update(next);
                }}
                placeholder="Title"
                className="w-auto flex-1"
              />
              <Input
                value={exp.start}
                onChange={(e) => {
                  const next = [...master.experiences];
                  next[index] = { ...exp, start: e.target.value };
                  update(next);
                }}
                placeholder="Start"
                className="w-24"
              />
              <Input
                value={exp.end}
                onChange={(e) => {
                  const next = [...master.experiences];
                  next[index] = { ...exp, end: e.target.value };
                  update(next);
                }}
                placeholder="End"
                className="w-24"
              />
              <button
                type="button"
                onClick={() => update(master.experiences.filter((_, i) => i !== index))}
                className="text-sm text-ink/40 hover:text-ink"
              >
                Remove
              </button>
            </div>
            <FactList
              sectionId={exp.id}
              facts={exp.facts}
              onChange={(facts) => {
                const next = [...master.experiences];
                next[index] = { ...exp, facts };
                update(next);
              }}
            />
          </div>
        ))}
        <Button
          type="button"
          variant="secondary"
          className="self-start"
          onClick={() => {
            const id = slugSectionId("EXP", usedSectionIds(master));
            update([
              ...master.experiences,
              { id, company: "", title: "", location: "", start: "", end: "", facts: [] },
            ]);
          }}
        >
          + Add experience
        </Button>
      </div>
    </section>
  );
}

function ProjectSection({ master, onChange }: Props) {
  const update = (next: Project[]) => onChange({ ...master, projects: next });
  const factCount = master.projects.reduce((n, p) => n + p.facts.length, 0);

  return (
    <section>
      <SectionHeading title="Projects" count={factCount} />
      <div className="flex flex-col gap-5">
        {master.projects.map((project, index) => (
          <div key={project.id} className="rounded-lg border border-em-softb p-4">
            <div className="mb-2 flex items-center gap-2">
              <Input
                value={project.name}
                onChange={(e) => {
                  const next = [...master.projects];
                  next[index] = { ...project, name: e.target.value };
                  update(next);
                }}
                placeholder="Project name"
                className="w-auto flex-1"
              />
              <button
                type="button"
                onClick={() => update(master.projects.filter((_, i) => i !== index))}
                className="text-sm text-ink/40 hover:text-ink"
              >
                Remove
              </button>
            </div>
            <div className="mb-3">
              <StringList
                items={project.tech}
                onChange={(tech) => {
                  const next = [...master.projects];
                  next[index] = { ...project, tech };
                  update(next);
                }}
                placeholder="Tech"
                addLabel="Add tech"
              />
            </div>
            <FactList
              sectionId={project.id}
              facts={project.facts}
              onChange={(facts) => {
                const next = [...master.projects];
                next[index] = { ...project, facts };
                update(next);
              }}
            />
          </div>
        ))}
        <Button
          type="button"
          variant="secondary"
          className="self-start"
          onClick={() => {
            const id = slugSectionId("PROJ", usedSectionIds(master));
            update([...master.projects, { id, name: "", tech: [], facts: [] }]);
          }}
        >
          + Add project
        </Button>
      </div>
    </section>
  );
}

function EducationSection({ master, onChange }: Props) {
  const update = (next: Education[]) => onChange({ ...master, education: next });

  return (
    <section>
      <SectionHeading title="Education" count={master.education.length} />
      <div className="flex flex-col gap-4">
        {master.education.map((edu, index) => (
          <div key={index} className="rounded-lg border border-em-softb p-4">
            <div className="mb-2 grid grid-cols-2 gap-2">
              <Input
                value={edu.school}
                onChange={(e) => {
                  const next = [...master.education];
                  next[index] = { ...edu, school: e.target.value };
                  update(next);
                }}
                placeholder="School"
              />
              <Input
                value={edu.degree}
                onChange={(e) => {
                  const next = [...master.education];
                  next[index] = { ...edu, degree: e.target.value };
                  update(next);
                }}
                placeholder="Degree"
              />
              <Input
                value={edu.location}
                onChange={(e) => {
                  const next = [...master.education];
                  next[index] = { ...edu, location: e.target.value };
                  update(next);
                }}
                placeholder="Location"
              />
              <Input
                value={edu.grad_date}
                onChange={(e) => {
                  const next = [...master.education];
                  next[index] = { ...edu, grad_date: e.target.value };
                  update(next);
                }}
                placeholder="Graduation date"
              />
            </div>
            <StringList
              items={edu.coursework}
              onChange={(coursework) => {
                const next = [...master.education];
                next[index] = { ...edu, coursework };
                update(next);
              }}
              placeholder="Course"
              addLabel="Add course"
            />
            <button
              type="button"
              onClick={() => update(master.education.filter((_, i) => i !== index))}
              className="mt-2 text-sm text-ink/40 hover:text-ink"
            >
              Remove
            </button>
          </div>
        ))}
        <Button
          type="button"
          variant="secondary"
          className="self-start"
          onClick={() =>
            update([
              ...master.education,
              { school: "", degree: "", location: "", grad_date: "", coursework: [] },
            ])
          }
        >
          + Add education
        </Button>
      </div>
    </section>
  );
}

function SkillsSection({ master, onChange }: Props) {
  const categories = Object.entries(master.skills);

  const setCategory = (category: string, skills: string[]) =>
    onChange({ ...master, skills: { ...master.skills, [category]: skills } });

  const renameCategory = (oldName: string, newName: string) => {
    const { [oldName]: skills, ...rest } = master.skills;
    onChange({ ...master, skills: { ...rest, [newName]: skills ?? [] } });
  };

  const removeCategory = (category: string) => {
    const { [category]: _removed, ...rest } = master.skills;
    onChange({ ...master, skills: rest });
  };

  return (
    <section>
      <SectionHeading
        title="Skills"
        count={categories.reduce((n, [, skills]) => n + skills.length, 0)}
      />
      <div className="flex flex-col gap-3">
        {categories.map(([category, skills]) => (
          <div key={category} className="flex flex-wrap items-center gap-2">
            <Input
              value={category}
              onChange={(e) => renameCategory(category, e.target.value)}
              className="w-40"
            />
            <StringList
              items={skills}
              onChange={(next) => setCategory(category, next)}
              placeholder="Skill"
              addLabel="Add skill"
            />
            <button
              type="button"
              onClick={() => removeCategory(category)}
              className="text-sm text-ink/40 hover:text-ink"
            >
              Remove category
            </button>
          </div>
        ))}
        <Button
          type="button"
          variant="secondary"
          className="self-start"
          onClick={() => setCategory("New category", [])}
        >
          + Add category
        </Button>
      </div>
    </section>
  );
}
