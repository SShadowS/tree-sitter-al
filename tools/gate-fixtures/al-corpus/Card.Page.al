page 50100 "Selftest Card"
{
    PageType = Card;
    SourceTable = "Selftest Customer";

    layout
    {
        area(Content)
        {
            group(General)
            {
                field("No."; Rec."No.")
                {
                    ApplicationArea = All;
                }
            }
            // validate --full Step 6c refuses a corpus with no link-family site
            part(Children; "Selftest Card")
            {
                ApplicationArea = All;
                SubPageLink = "Parent No." = field("No.");
            }
        }
    }

    actions
    {
        area(Processing)
        {
            action(DoIt)
            {
                ApplicationArea = All;

                trigger OnAction()
                begin
                    Message('done');
                end;
            }
        }
    }
}
