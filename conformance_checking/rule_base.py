from datetime import datetime
import numpy as np


class Rule_Checker:
    def get_percentage(self, total: int, observations: int) -> float:
        return round((100 / total) * observations, 4)

    def export_case_ids(self, file: str, ids: list):
        file = file + ".csv"
        with open(file, "w") as f:
            for case_id in ids:
                f.write("%s\n" % case_id)
            f.close()

    def check_cardinality(self, log, activity: str, upper: int, lower: int) -> dict:
        """
        Check cardinalities for given activity.

        :param log: event log
        :param activity: name of the activity
        :param upper: max. number of occurrence in one trace, -1 if infinite
        :param lower: min. number of occurrence in one trace
        :return: report
        """

        violation_upper = 0
        violation_lower = 0

        for trace in log:

            events = trace["events"]
            counter = events.count(activity)

            if counter < lower:
                violation_lower += 1
            elif counter > upper != -1:
                violation_upper += 1

        return {
            "activity": activity,
            "violation upper": (
                violation_upper,
                self.get_percentage(len(log), violation_upper),
            ),
            "violation lower": (
                violation_lower,
                self.get_percentage(len(log), violation_lower),
            ),
        }

    def check_order_loop_count(self, log, first: str, second: str, file="") -> dict:

        trace_ids = []

        violations = 0
        traces = 0

        for trace in log:
            events = trace["events"]

            first_counter = 0
            second_counter = 0

            for event in events:
                if event == first:
                    first_counter += 1
                if event == second:
                    second_counter += 1

            if first_counter != second_counter:
                violations += 1

                trace_ids.append(",".join([trace["trace_id"]]))

            traces += 1

        if len(file) > 0:
            file = "_".join([file, "order_loop_count", first, second])
            self.export_case_ids(file, trace_ids)

        return {
            "first": first,
            "second": second,
            "violations": (violations, self.get_percentage(traces, violations)),
        }

    def check_rir_rgr(self, log, file="") -> dict:
        first = "Record Goods Receipt"
        second = "Record Invoice Receipt"

        trace_ids = []

        violations = 0
        traces = 0

        for trace in log:
            events = trace["events"]

            first_counter = 0
            second_counter = 0

            failed = False

            for event in events:
                if event == first:
                    if second_counter > first_counter:
                        violations += 1
                        trace_ids.append(
                            ",".join([trace["trace_id"], str(len(events))])
                        )
                        failed = True
                        break
                    else:
                        first_counter += 1
                elif event == second:
                    second_counter += 1

            traces += 1

        if len(file) > 0:
            file = "_".join([file, "order_RIR_before_RGR"])
            self.export_case_ids(file, trace_ids)

        return {
            "first": first,
            "second": second,
            "violations": (violations, self.get_percentage(traces, violations)),
        }

    def check_rgr_ci(self, log, file="") -> dict:
        first = "Record Goods Receipt"
        second = "Clear Invoice"

        trace_ids = []

        violations = 0
        traces = 0

        for trace in log:
            events = trace["events"]

            first_counter = 0
            second_counter = 0

            failed = False

            for event in events:
                if event == first:
                    if second_counter > first_counter:
                        violations += 1
                        trace_ids.append(
                            ",".join([trace["trace_id"], str(len(events))])
                        )
                        failed = True
                        break
                    else:
                        first_counter += 1
                elif event == second:
                    second_counter += 1

            traces += 1

        if len(file) > 0:
            file = "_".join([file, "order_RGR_before_CI"])
            self.export_case_ids(file, trace_ids)

        return {
            "first": first,
            "second": second,
            "violations": (violations, self.get_percentage(traces, violations)),
        }

    def check_rir_ci(self, log, file="", with_throughput=False) -> dict:
        first = "Record Invoice Receipt"
        second = "Clear Invoice"

        avg, median, _, _ = self.make_throughout_analysis(log, first, second)[
            "throughput"
        ]

        if avg > median:
            throughput_time = avg
            if with_throughput:
                print("Take throughput time (mean) into account: ", throughput_time)
        else:
            throughput_time = median
            if with_throughput:
                print("Take throughput time (median) into account: ", throughput_time)

        trace_ids = []

        violations = 0
        traces = 0

        for trace in log:
            events = trace["events"]

            first_counter = 0
            second_counter = 0

            first_stack = []
            second_stack = []

            failed = False
            hadCI = False
            lastCI = False

            for i, event in enumerate(events):
                if event == first:
                    lastCI = False
                    if second_counter > first_counter:
                        violations += 1
                        trace_ids.append(
                            ",".join([trace["trace_id"], str(len(events))])
                        )
                        failed = True
                        break
                    else:
                        first_counter += 1
                        first_stack.append(trace["events_with_ts"][i]["timestamp"])
                elif event == second:
                    hadCI = True
                    lastCI = True
                    second_counter += 1
                    second_stack.append(trace["events_with_ts"][i]["timestamp"])

            if not failed:
                if with_throughput:
                    if first_counter > second_counter:
                        max_datetime = datetime(2018, 12, 31, 23, 59, 59).replace(
                            tzinfo=None
                        )

                        days = (
                            max_datetime.replace(tzinfo=None)
                            - first_stack[-1].replace(tzinfo=None)
                        ).days

                        if days <= int(throughput_time):
                            violations += 1
                            trace_ids.append(
                                ",".join([trace["trace_id"], str(len(events))])
                            )

                    elif first_counter != second_counter:
                        violations += 1
                        trace_ids.append(
                            ",".join([trace["trace_id"], str(len(events))])
                        )
                elif first_counter != second_counter and hadCI:
                    violations += 1
                    trace_ids.append(",".join([trace["trace_id"], str(len(events))]))

            traces += 1

        if len(file) > 0:
            file = "_".join(
                [
                    file,
                    "order_RIR_before_CI",
                    "with_with_throughput" if with_throughput else "without_throughput",
                ]
            )
            print("File-Name: ", file)
            self.export_case_ids(file, trace_ids)

        return {
            "first": first,
            "second": second,
            "violations": (violations, self.get_percentage(traces, violations)),
        }

    def make_throughout_analysis(self, log, first: str, second: str, file = "") -> dict:
        violations = 0
        traces = 0

        throughput = []

        output = []

        for trace in log:
            events = trace["events_with_ts"]

            first_stack = []
            second_stack = []

            first_counter = 0
            second_counter = 0

            failed = False
            hadCI = False

            for event_ts in events:
                event = event_ts["name"]
                timestamp = event_ts["timestamp"]
                if event == first:
                    if second_counter > first_counter:
                        violations += 1
                        failed = True
                        break
                    else:
                        first_counter += 1
                        first_stack.append(timestamp)
                elif event == second and first_counter > second_counter:
                    hadCI = True
                    second_counter += 1
                    second_stack.append(timestamp)

                    delta = (
                        second_stack[second_counter - 1]
                        - first_stack[second_counter - 1]
                    )

                    throughput.append(delta.days)
                    output.append(",".join([trace["trace_id"], str(delta.days), str(second_counter), str(traces)]))

            if not failed and hadCI:
                if first_counter != second_counter:
                    violations += 1

            traces += 1

        if len(file) > 0:
            file = "_".join(
                [
                    file,
                    "throughput", first, second
                ]
            )
            print("File-Name: ", file)
            self.export_case_ids(file, output)

        return {
            "first": first,
            "second": second,
            "throughput": (
                np.average(throughput),
                np.median(throughput),
                np.std(throughput),
                np.var(throughput),
            ),
        }

    # Legacy methods

    def check_order(self, log, first: str, second: str) -> dict:
        """
        Check the order of the given activities.

        :param log: event log
        :param first: activity
        :param second: activity
        :return: report
        """

        violations = 0
        traces = 0

        for trace in log:
            events = trace["events"]
            first_stack = []

            if first in events and second in events:
                traces += 1

                for event in events:
                    if event == first:
                        first_stack.append(event)
                    elif event == second and len(first_stack) == 0:
                        violations += 1

        return {
            "first": first,
            "second": second,
            "violations": (violations, self.get_percentage(traces, violations)),
        }

    def check_response(
        self, log, request: str, response: str, single_occurrence=False
    ) -> dict:
        """
        Check response requirements of the given activity.


        :param log: event log
        :param request: activity which expects a requested activity
        :param response: requested activity
        :param single_occurrence: specifies whether a single occurrence of the
        responding activity already satisfies the rule
        :return: report
        """

        violations = 0
        candidate_traces = 0
        violated_traces = 0

        for trace in log:
            events = trace["events"]
            req_stack = []

            tracked = False

            if request in events:
                candidate_traces += 1
                if single_occurrence:
                    if response in events:
                        req_idx = events[::-1].index(request)
                        res_idx = events[::-1].index(response)
                        if req_idx < res_idx:
                            violations += 1
                            violated_traces += 1
                    else:
                        violated_traces += 1
                        violations += 1
                else:
                    for event in events:
                        if event == request:
                            req_stack.append(event)
                        elif event == response and len(req_stack) > 0:
                            req_stack.pop()
                    if len(req_stack) > 0:
                        violated_traces += 1
                        violations += len(req_stack)

        return {
            "request": request,
            "response": response,
            "violations": (
                violations,
                violated_traces,
                self.get_percentage(candidate_traces, violated_traces),
            ),
            "single": single_occurrence,
        }

    def check_precedence(
        self, log, preceding: str, request: str, single_occurrence=False, file=""
    ) -> dict:
        """
        Check precedence requirements of the given activity.

        :param log: event log
        :param preceding: activity that should precede the requesting activity
        :param request: requesting activity
        :param single_occurrence: specifies whether a single occurrence of the
        preceding activity already satisfies the rule
        :return: report
        """

        violations = 0
        candidate_traces = 0
        trace_ids = []
        violated_traces = 0

        for trace in log:
            events = trace["events"]
            pre_stack = []
            tracked = False

            if request in events:
                candidate_traces += 1
                if single_occurrence:
                    if preceding in events:
                        request_idx = events.index(request)
                        preceding_idx = events.index(preceding)
                        if request_idx < preceding_idx:
                            violations += 1
                            violated_traces += 1
                            trace_ids.append(
                                ",".join(
                                    [
                                        trace["trace_id"],
                                        trace["vendor"],
                                        trace["value"],
                                        trace["spend_area"],
                                        trace["item_type"],
                                    ]
                                )
                            )
                    else:
                        trace_ids.append(
                            ",".join(
                                [
                                    trace["trace_id"],
                                    trace["vendor"],
                                    trace["value"],
                                    trace["spend_area"],
                                    trace["item_type"],
                                ]
                            )
                        )
                        violations += 1
                        violated_traces += 1
                else:
                    for event in events:
                        if event == preceding:
                            pre_stack.append(event)
                        elif event == request and len(pre_stack) > 0:
                            pre_stack.pop()
                        elif event == request:
                            violations += 1
                            if not tracked:
                                trace_ids.append(
                                    ",".join(
                                        [
                                            trace["trace_id"],
                                            trace["vendor"],
                                            trace["value"],
                                            trace["spend_area"],
                                            trace["item_type"],
                                        ]
                                    )
                                )
                                violated_traces += 1
                                tracked = True
        if len(file) > 0:
            file = "_".join(
                [file, "precedence", preceding, request, str(single_occurrence)]
            )
            self.export_case_ids(file, trace_ids)

        return {
            "preceding": preceding,
            "request": request,
            "violations": (
                violations,
                violated_traces,
                self.get_percentage(candidate_traces, violated_traces),
            ),
            "single": single_occurrence,
        }

    def check_exclusive(self, log, first_activity: str, second_activity: str) -> dict:
        """
        Check the exclusiveness of two activities.


        :param log: event log
        :param first_activity: activity
        :param second_activity: activity
        :return: report
        """

        violations = 0
        violated_traces = 0

        for trace in log:
            events = trace["events"]

            if first_activity in events and second_activity in events:
                violated_traces += 1
                violations += 1

        return {
            "first activity": first_activity,
            "second activity": second_activity,
            "violations": (violations, self.get_percentage(len(log), violated_traces)),
        }
