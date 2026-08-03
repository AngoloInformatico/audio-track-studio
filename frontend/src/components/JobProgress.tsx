import type { JobView } from "../types/audio";

interface JobProgressProps {
  job: JobView<unknown>;
  cancelledText?: string;
}

export function JobProgress({ job, cancelledText }: JobProgressProps) {
  return (
    <div className={`job-progress ${job.status}`}>
      <div>
        <span>{job.status === "failed" ? "Operazione non riuscita" : job.message}</span>
        <strong>{Math.round(job.progress)}%</strong>
      </div>
      <div className="job-progress-track"><span style={{ width: `${job.progress}%` }} /></div>
      {job.error && <p>{job.error}</p>}
      {job.status === "cancelled" && <p>{cancelledText ?? "L’operazione è stata annullata."}</p>}
    </div>
  );
}
